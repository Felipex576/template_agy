from pyspark.sql import DataFrame, SparkSession
from src.config.logger import logger
from src.utils.constants import QueryConstants
from datetime import date
from src.transformations.bank_processor import BankProcessor
from src.transformations.t_1_processor import T1Processor 
from typing import Tuple, List, Callable, Any


class QueryBuilder:

    def __init__(self, spark: SparkSession, rtbcol_database: str, unity_database: str, 
                 trm_database: str, dominus_database: str, mambu_cc_database: str, 
                 checking_accounts_database: str, adapter_database: str, 
                 unity_operations_table: str):
        self.spark = spark
        self.bank_processor = BankProcessor(self.spark)
        self.t1_processor = T1Processor(self.spark)
        self.rtbcol_database = rtbcol_database
        self.unity_database = unity_database
        self.trm_database = trm_database
        self.dominus_database = dominus_database
        self.mambu_cc_database = mambu_cc_database
        self.checking_accounts_database = checking_accounts_database
        self.adapter_database = adapter_database
        self.unity_operations_table = unity_operations_table
     
    @staticmethod    
    def normalize_dates(date_list: List) -> str: 
        """Format list of dates as SQL date literals."""
        return ", ".join(
            f"DATE '{d}'"
            for d in date_list
        )
             
    def date_between_fix(self, start_date: List, function: Callable, column: str) -> Tuple[str, List, List]:
        """Build SQL BETWEEN conditions for pairs of calculated dates."""
        one_list = []
        two_list = []

        for item_date in start_date: 
            date_one, date_two = function(item_date)
            one_list.append(date_one)
            two_list.append(date_two)
            
        return " OR ".join(
            f"""(
                {column} BETWEEN DATE '{start}'
                            AND DATE '{end}'
            )"""
            for start, end in zip(one_list, two_list)
        ), one_list, two_list
    
    def get_bank_data(self, date_list: List, previous_list: List, bank_table: str) -> Tuple[DataFrame, List]:
        """
        Query bank daily balance data for specified dates.

        Args:
            date_list (List): List of report dates.
            previous_list (List): List of previous business dates.
            bank_table (str): Bank daily balance table name.

        Returns:
            Tuple[DataFrame, List]: Bank balance DataFrame and list of adjusted previous dates.
        """
        previous_dates = []
        for start_date, final_date in zip(date_list, previous_list):
            previous_date = self.bank_processor.get_previous_date(start_date, final_date)
            previous_date = self.bank_processor.adjust_year_end_dates(start_date, previous_date)
            
            previous_dates.append(previous_date)
                
        date_list_sql = self.normalize_dates(previous_dates)
        
        query = f"""
            SELECT numero_cuenta, nombre_titular_cuenta, nombre_banco,
            tipo_cuenta, saldo_bancario_final, saldo_en_canje, fecha_movimiento  
            FROM glue_catalog.{self.rtbcol_database}.{bank_table} 
            WHERE fecha_movimiento IN ({date_list_sql})  
        """
        
        logger.info("Executing bank query: " + query)
        
        return self.spark.sql(query), previous_dates
    
    def get_money_market_data(self, start_date: List, money_market_table: str) -> DataFrame:
        """
        Query money market operations joined with unity operations for specified dates.

        Args:
            start_date (List): List of report dates.
            money_market_table (str): Money market table name.

        Returns:
            DataFrame: Money market operations DataFrame.
        """     
        date_list_sql = self.normalize_dates(start_date)
                 
        query = f"""
            SELECT mm.fecha_operacion, mm.fecha_cumplimiento, mm.cod_central_deposito,
            mm.clasificacion, mm.tipo_sim, mm.codigo_especie, mm.nemotecnico,
            mm.tipo_operacion, mm.genera_detalle, mm.valor_de_giro, ou.fecha_cuadre
            FROM glue_catalog.{self.rtbcol_database}.{money_market_table} mm
            JOIN glue_catalog.{self.unity_database}.{self.unity_operations_table} ou
            ON mm.consecutivo = ou.consecutivo
            WHERE ou.fecha_cuadre IN ({date_list_sql}) 
            AND mm.tipo_operacion IN ({QueryConstants.OPERATION_TYPE})
        """
        
        logger.info("Executing money market query: " + query)
        
        return self.spark.sql(query)

    def get_unity_data(self, start_date: List, movements_table: str, master_table: str) -> Tuple[DataFrame, DataFrame, List, List]:
        """
        Query unity account movements and master homologation data.

        Args:
            start_date (List): List of report dates.
            movements_table (str): Unity account movements table name.
            master_table (str): Master homologation table name.

        Returns:
            Tuple[DataFrame, DataFrame, List, List]: Unity movements DataFrame, master DataFrame, and date lists.
        """
        date_conditions, one_list, two_list = self.date_between_fix(start_date, self.t1_processor.first_business_day, "m.fecha")
                          
        query_one = f"""
            SELECT m.concepto, o.clasificacion, o.liquidacion, o.tipo_operacion,
            o.fecha_futura, m.valor, m.cod_tipo_movimiento, m.fecha, 
            m.cuenta_bancaria, m.rendimiento
            FROM glue_catalog.{self.unity_database}.{movements_table} m
            LEFT JOIN glue_catalog.{self.unity_database}.{self.unity_operations_table} o
            ON m.operacion = o.consecutivo
            WHERE {date_conditions} 
        """
        
        logger.info("Executing unity query: " + query_one)
        
        query_two = f"""
            SELECT mh.codigo_contable, mh.codigo_cud, mh.concepto_cud
            FROM glue_catalog.{self.rtbcol_database}.{master_table} mh
        """
        logger.info("Executing maestro homologacion unity query: " + query_two)
        
        return self.spark.sql(query_one), self.spark.sql(query_two), one_list, two_list
           
    def get_transacctions_data(self, start_date: List, multicash_table: str, umbrella_table: str) -> Tuple[DataFrame, List, List]:
        """
        Query multicash movements filtered by umbrella accounts for specified dates.

        Args:
            start_date (List): List of report dates.
            multicash_table (str): Multicash movements table name.
            umbrella_table (str): Umbrella master accounts table name.

        Returns:
            Tuple[DataFrame, List, List]: Bank transactions DataFrame and date lists.
        """
        date_conditions, one_list, two_list = self.date_between_fix(start_date, self.t1_processor.last_business_day, "m.fecha_mvto")
        
        query = f"""
            SELECT m.cuenta_bancaria, m.moneda, m.monto, m.fecha_mvto
            FROM glue_catalog.{self.rtbcol_database}.{multicash_table} m
            INNER JOIN glue_catalog.{self.rtbcol_database}.{umbrella_table} c
            ON m.cuenta_bancaria = regexp_replace(c.cuenta_bancaria, '^0+', '')
            WHERE {date_conditions}
            AND c.titular = 'BANCO BTG PACTUAL COLOMBIA SA' 
            AND c.estado = 'ACTIVA'
        """
        
        logger.info("Executing transactions query: " + query)
        
        return self.spark.sql(query), one_list, two_list
    
    def get_trm_data(self, start_date: List, trm_table: str) -> DataFrame:
        """
        Query TRM values valid for specified dates.

        Args:
            start_date (List): List of report dates.
            trm_table (str): TRM table name.

        Returns:
            DataFrame: TRM records DataFrame.
        """
        date_list_sql = self.normalize_dates(start_date)
                                    
        query = f"""
            WITH dates AS (
                SELECT *
                FROM (
                    VALUES {date_list_sql}
                ) AS t(start_date)
            )
        
            SELECT t.valor, d.start_date as fecha
            FROM glue_catalog.{self.trm_database}.{trm_table} t
            JOIN dates d
            ON t.vigencia_desde <= d.start_date
            AND t.vigencia_hasta >= d.start_date
        """
        
        logger.info("Executing trm query: " + query)
        
        return self.spark.sql(query)
        
    def get_cdt_data(self, start_date: List, renewals_table: str) -> DataFrame:
        """
        Query CDT renewal operations for specified dates.

        Args:
            start_date (List): List of report dates.
            renewals_table (str): CDT renewals table name.

        Returns:
            DataFrame: CDT renewals DataFrame.
        """
        date_list_sql = self.normalize_dates(start_date)   
                            
        query = f"""
            SELECT total_renovacion, fecha_operacion
            FROM glue_catalog.{self.dominus_database}.{renewals_table} 
            WHERE fecha_operacion IN ({date_list_sql})             
        """
        
        logger.info("Executing cdt query: " + query)
        
        return self.spark.sql(query)
    
    def get_repurchase_data(self, start_date: List, operations_a_table: str, operations_b_table: str) -> DataFrame:
        """
        Query repurchase and issuance operations (types A and B) for specified dates.

        Args:
            start_date (List): List of report dates.
            operations_a_table (str): Dominus operations type A table name.
            operations_b_table (str): Dominus operations type B table name.

        Returns:
            DataFrame: Repurchase and issuance operations DataFrame.
        """
        date_list_sql = self.normalize_dates(start_date)
                            
        query = f"""
            SELECT a.codigo_isin, a.fecha_operacion, b.saldo, a.precio_contado, 
            b.tipo_participacion, b.nombre_inversion, a.fecha_inicio, a.fecha_fin
            FROM glue_catalog.{self.dominus_database}.{operations_a_table} a
            JOIN glue_catalog.{self.dominus_database}.{operations_b_table} b
            ON a.id = b.id_padre
            WHERE a.codigo_isin LIKE '{QueryConstants.IS_IN}%'  
            AND b.tipo_participacion IN (1, 2)
            AND b.nombre_inversion = '{QueryConstants.NAME}'
            AND a.fecha_operacion IN ({date_list_sql}) 
            AND a.fecha_inicio IN ({date_list_sql})            
        """
        
        logger.info("Executing repurchase query: " + query)
        
        return self.spark.sql(query)
        
    def get_pyg_derivatives_data(self, previous_date: List, derivatives_table: str) -> DataFrame:
        """
        Query standardized derivatives profit/loss data for specified dates.

        Args:
            previous_date (List): List of previous business dates.
            derivatives_table (str): Standardized derivatives table name.

        Returns:
            DataFrame: Derivatives P&G DataFrame.
        """
        date_list_sql = self.normalize_dates(previous_date)
                            
        query = f"""
            SELECT descripcion, tipo_cumplimiento, utilidad, fecha_inicial 
            FROM glue_catalog.{self.rtbcol_database}.{derivatives_table}
            WHERE descripcion = '{QueryConstants.DESCRIPTION}'
            AND tipo_cumplimiento = '{QueryConstants.COMPLIANCE_TYPE}'
            AND fecha_inicial IN ({date_list_sql})
        """
        
        logger.info("Executing pyg query: " + query)
        
        return self.spark.sql(query)
    
    def get_ach_cycle_data(self, start_date: List, accounts_table: str, transactions_table: str, channels_table: str) -> DataFrame:
        """
        Query Mambu ACH cycle transactions joined with accounts and channels for specified dates.

        Args:
            start_date (List): List of report dates.
            accounts_table (str): Mambu accounts table name.
            transactions_table (str): Mambu transactions table name.
            channels_table (str): Mambu channels table name.

        Returns:
            DataFrame: ACH cycle transactions DataFrame.
        """
        date_list_sql = self.normalize_dates(start_date)      
                  
        query = f"""
            WITH unique_accounts AS (
                SELECT *
                FROM (
                    SELECT
                        a.clave_codificada, a.id,
                        ROW_NUMBER() OVER (
                            PARTITION BY a.clave_codificada
                            ORDER BY a.fecha_ultima_modificacion DESC
                        ) AS rn
                    FROM glue_catalog.{self.mambu_cc_database}.{accounts_table} a
                ) x
                WHERE rn = 1
            )

            SELECT c.nombre AS canal, t.monto, t.fecha_hora_valor, a.id, t.fecha_valor
            FROM glue_catalog.{self.mambu_cc_database}.{transactions_table} t
            INNER JOIN unique_accounts a
            ON t.clave_cuenta_padre = a.clave_codificada
            INNER JOIN glue_catalog.{self.mambu_cc_database}.{channels_table} c
            ON t.detalles_transaccion_clave_canal_transaccion = c.clave_codificada
            WHERE t.fecha_valor IN ({date_list_sql})
        """
        
        logger.info("Executing ach cycle query: " + query)
        
        return self.spark.sql(query)
    
    def get_ach_balance_data(self, start_date: List, previous_date: List, balance_table: str, deposit_table: str) -> DataFrame:
        """
        Query ACH deposit account balance sums for specified dates.

        Args:
            start_date (List): List of report dates.
            previous_date (List): List of previous business dates.
            balance_table (str): Balance table name.
            deposit_table (str): Deposit account table name.

        Returns:
            DataFrame: Grouped ACH balance DataFrame.
        """
        date_list_sql = self.normalize_dates(start_date)
        previous_list_sql = self.normalize_dates(previous_date)
                            
        query = f"""
            SELECT b.fecha_saldo, SUM(COALESCE(b.total_balance, 0.0)) AS total_balance
            FROM glue_catalog.{self.checking_accounts_database}.{balance_table} b
            JOIN glue_catalog.{self.checking_accounts_database}.{deposit_table} c
            ON b.id_cuenta = c.id_cuenta_deposito
            WHERE (b.fecha_saldo IN ({date_list_sql})
            OR b.fecha_saldo IN ({previous_list_sql}))
            AND c.id_producto IN ({QueryConstants.PRODUCT_ID})
            GROUP BY b.fecha_saldo
            ORDER BY b.fecha_saldo DESC
        """        
        logger.info("Executing ach balance query: " + query)
        
        return self.spark.sql(query)
    
    def get_ach_data(self, start_date: List, previous_date: List, adaptor_table: str) -> DataFrame:
        """
        Query adaptor reconciliation transactions for specified dates.

        Args:
            start_date (List): List of report dates.
            previous_date (List): List of previous business dates.
            adaptor_table (str): Adaptor reconciliation table name.

        Returns:
            DataFrame: Adaptor reconciliation DataFrame.
        """
        date_list_sql = self.normalize_dates(start_date)
        previous_list_sql = self.normalize_dates(previous_date)
                            
        query = f"""
            SELECT transaction_type, name, status, reg6_cuenta_receptora, 
            reg5_entidad_originadora, reg5_nombre_originador, reg6_entidad_receptora, 
            reg6_nombre_cliente_receptor, reg6_valor_transaccion, fecha_consulta 
            FROM glue_catalog.{self.adapter_database}.{adaptor_table}
            WHERE fecha_consulta IN ({date_list_sql})
            OR fecha_consulta IN ({previous_list_sql}) 
        """
        
        logger.info("Executing ach query: " + query)
        
        return self.spark.sql(query)