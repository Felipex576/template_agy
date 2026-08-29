REQUIRED_JOB_ARGS = [
    "JOB_NAME",
    "RTBCOL_DATABASE",
    "UNITY_DATABASE",
    "TRM_DATABASE",
    "DOMINUS_DATABASE",
    "MAMBU_CC_DATABASE",
    "CHECKING_ACCOUNTS_DATABASE",
    "ADAPTER_DATABASE",
    "UNITY_OPERATIONS_TABLE",
    "BANK_BALANCES_TABLE",
    "MONEY_MARKET_TABLE",
    "CC_MOVEMENTS_TABLE",
    "MASTER_HOMOLOGATION_TABLE",
    "MULTICASH_MOVEMENTS_TABLE",
    "UMBRELLA_MASTER_TABLE",
    "TRM_TABLE",
    "RENEWAL_OPERATIONS_TABLE",
    "OPERATIONS_A_TABLE",
    "OPERATIONS_B_TABLE",
    "STANDARDIZED_DERIVATIVES_TABLE",
    "MAMBU_ACCOUNTS_TABLE",
    "MAMBU_TRANSACTIONS_TABLE",
    "MAMBU_CHANNELS_TABLE",
    "BALANCE_TABLE",
    "DEPOSIT_ACCOUNT_TABLE",
    "RECONCILIATION_ADAPTER_TABLE",
    "INCOME_TABLE",
    "EXPENSE_TABLE",
    "AVAILABLE_TABLE",
    "SUMMARY_TABLE",
    "MARKET_DATABASE",
    "CHRONOS_BUCKET_NAME",
    "COMPANY",
    "REPORT_DATE",
    "REPORT_TYPE",
    "TRUSTED_BUCKET",
    "PREFIX_DATA",
    "PREFIX_FILE",
    "OUTPUT_FILE_PATH",
    "PROJECT_BUCKET_NAME"
]

class QueryConstants:
    """Static query values."""
    DESCRIPTION = "BANCO BTG PACTUAL COLOMBIA SA"
    COMPLIANCE_TYPE = "F"
    ACCOUNT_TYPES = ['Cuenta corriente PE', 'Cuenta corriente PJ', 'Cuenta corriente PN']
    OPERATION_TYPE = "'C', 'V'"
    PRODUCT_ID = """
    '8a9b94ca7e6df00a017e7de910180007', 
    '8a9b94ca7e6df00a017e7deb1024000d',  
    '8a9b94ca7e6df00a017e7def61b70016'
    """
    NAME = "BANCO BTG PACTUAL COLOMBIA S.A"
    IS_IN = "COB70CD"


class BankConstants:
    """Constants for bank processing and balance categorization."""
    BANREP_NO_REM = 0.0
    COMMERCIAL_COP = 0.0
    COMMERCIAL_USD = 0.0
    HOLDER_NAME = "BANCO BTG PACTUAL COLOMBIA SA"

    BANREP_NOREM90 = "62015990"
    BANREP_NOREM91 = "62015991"
    BANREP_REM =  "64011480"

    BALANCE_ACCOUNT = {
        "ahorro_dav": ["570033570004227"],
        "ahorro_occ": ["423816990"],
        "ahorro_bog": ["434381323"],
        "ahorro_banc": ["61100001577"],
        "adm_dav": ["560033569994602", "560033569994594"],
        "adm_bog": ["434394037", "434394045"],
        "adm_banc": ["61100001064", "61100001065", "61100001369", "61100001576"]
        }

    USD_ACCOUNTS = {
        "dol_cayman": "86110",
        "dol_bofa": "1901751916",
        "dol_citi": "14674340",
        "dol_citi_usd": "36442812",
        "dol_citi2": "36506441",
        "dol_bancol_panama": "80110003748",
        "bradesco": "30863139"
        }
    
    AVAILABLE_T0 = "disponible_t-0"
    AVAILABLE_T1 = "disponible_t-1"
    
class BankTranscConstants:
    """Constants used in bank transactions processing."""
    EXCLUDE_ACCOUNTS = ["62015991", "62015990", "64011480"]
    CURRENCY_COP = "COP"
    CURRENCY_USD = "USD"

class MoneyMarketConstants:
    """Constants used in money market processing."""
    SIM = "SIM"
    NORMAL = "NORMAL"
    REPO = "REPO"
    TTV = "TTV"
    CENTRAL_DEPOSITORIES = ["DCV", "DVL"]
    SIM_ACTIVE = "A"
    SIM_PASSIVE = "P"
    OPERATION_BUY = "C"
    OPERATION_SELL = "V"
    SPECIES_TES_PATTERN = "CT"
    SPECIES_PRIVATE_PATTERN = "CA|CB|CD|CH|CI|CP|CS|MM"
    MONEY_MARKET_NEMO = "MONEYMARKET"
    GENERATE_DETAIL_YES = "SI"

class UnityConstants:
    """Constants used in unity processing."""
    INCOME_BREB = 0.0
    EXPENSE_BREB = 0.0

    EXCHANGE_SEBRA = "DIVISAS SEBRA"
    OPERATIONS = "OPERACIONES DVP DECEVAL"
    ISSUING_PAYMENTS = "APR.PAGOS DE EMISORES S/ TÍTULOS VA"
    PAYMENT_RETURNS = "PAGO RENDIMIENTOS"
    DERIVATIVES_OTC = "DERIVADOS OTC"
    THIRD_HEADING = "APR ENTR CTA DEPÓS DIFER TITULAR-TERCERO"

    OTHER_INCOME = [
        "APR. OP CON DECEVAL RECURSOS PROPIOS",
        "APR. OP CON DCV RECURSOS PROPIOS",
        "AP.ENTRE CUENTAS DE DEP. DE LA MISMA ENT",
        "TRANSFERENCIA DE FONDOS PARA OPERAC",
        "APR. ENTRE CTAS DEPÓS. DIFERENTE TI",
        "APR OP ESPEC MERC SECUN RENTA VARIA",
        "APR.CONSTITUCION INTERBANCARIOS INT",
        "APR. OP CON TÍTULOS DEPOSITADOS EN DCV",
        "TRANSFERENCIA DE FONDOS PARA OPERACIONES FICS - BANCO COMERCIAL Y CUSTODIO",
        "APR.CONSTITUCION INTERBANCARIOS INTRADIA",
        "A.DESEMBOLSOS DE CREDITO - ESTABLECIMIEN",
        "APR OP ESPEC MERC SECUN RENTA VARIAB BVC"
    ]

    GMF_CONCEPT = "G.M.F. SOBRE LA TRANSACCIÓN"
    INTEREST_PAYMENTS = "A.PAGOS POR CAP. E INTERESES SOBRE CRÉDI"

    EXPENSE_SEBRA = [
        "DB TARIFA TRANSACCIONAL CUD",
        "AP. SERVICIOS CRCC - PD",
        "DB IVA",
        "DB PAGO DE TARIFAS DCV",
        "DB TARIFA ADMINISTRACION DE CUENTAS",
        "DB TARIFA PUNTOS S.E.B.R.A",
        "DB TARIFAS SEN"
    ]

    OTHER_OPS = [
        "AP. CONSTITUCION GARANTIA POR POSIC",
        "AP. DEVOLUCION GARANTIA EXTRAORDINA",
        "AP. CONSTITUCION GARANTIA EXTRAORDI",
        "AP. DEVOLUCION GARANTIA POR POSICIO",
        "AP. LIQUIDACION DIARIA OPERACIONES",
        "INTERESES REMUNERADO"
    ]
    
    NORMAL = "NORMAL"
    SB = "SB"
    OF = "OF"
    SIM = "SIM"
    VV = "V" 
    CC = "C"
    TTV = "TTV"
    REPO = "REPO"
    LIQUIDATION = [44206, 43422, 43420]
    OP_TYPE = [45495, 45435, 44495, 44435]
    CLASIFY = [44211, 44481, 45431] 
    CONCEPT = [310, 389, 366, 362]
    LIT_CONCEPT = [
        "PAGO RENDIMIENTOS", "DIVISAS SEBRA", 
        "DERIVADOS OTC", "INTERESES REMUNERADO"]
    
    ND = "ND"

class T1MarketConstants:
    """Constants used in t1 money market today processing."""
    SIM = "SIM"
    NORMAL = "NORMAL"
    REPO = "REPO"
    TTV = "TTV"

    CENTRAL_DEPOSITORIES = ["DCV", "DVL"]

    SIM_ACTIVE = "A"
    SIM_PASSIVE = "P"

    OPERATION_BUY = "C"
    OPERATION_SELL = "V"

    SPECIES_TES_PATTERN = "CT"
    SPECIES_PRIVATE_PATTERN = "CA|CB|CD|CH|CI|CP|CS|MM"

    MONEYMARKET = "MONEYMARKET"
    GENERATE_DETAIL_YES = "SI"

    DEFAULT_REGISTER_STATUS = "Without registers"

class CdtConstants:
    """Constants used in cdt processing."""

    IS_IN_CODE = "COB70CD"
    ISIN_CODE_BONOS = "COB70CB"
    PARTICIPATION_TYPE_REPURCHASE = "1"
    PARTICIPATION_TYPE_ISSUANCE = "2"
    INVESTMENT_NAME = "BANCO BTG PACTUAL COLOMBIA S.A"

class CycleConstants:
    """Constants used in cycle ach processing."""

    WITHDRAWALS_ACH = [0.0, 0.0, 0.0, 0.0, 0.0]
    DEPOSIT_ACH = [0.0, 0.0, 0.0, 0.0, 0.0]
    WITHDRAWALS_REVERSALS = [0.0, 0.0, 0.0, 0.0, 0.0]
    DEBIT_SEBRA = 0.0
    CREDIT_SEBRA = 0.0
    DEBIT_RETURNS_SEBRA = 0.0
    CREDIT_RETURNS_SEBRA = 0.0

    ACH_WITHDRAWAL = "RETIRO ACH"
    ACH_DEPOSIT = "DEPOSITO ACH"
    ACH_RETURN = "DEVOLUCION RETIRO ACH"
    
    CONCEPTS_ACH = [ACH_WITHDRAWAL, ACH_DEPOSIT, ACH_RETURN]

    DEBIT_TRANSFER_SEBRA = "TRASLADO FONDOS SEBRA DEBITO"
    CREDIT_TRANSFER_SEBRA = "TRASLADO FONDOS SEBRA CREDITO"
    RETURN_DEBIT_FUNDS_SEBRA = "DEVOLUCION TRASLADO FONDOS SEBRA DEBITO"
    RETURN_CREDIT_FUNDS_SEBRA = "DEVOLUCION TRASLADO FONDOS SEBRA CREDITO"

    WITHDRAWAL_SLOTS = [
        ("00:00:00", "08:31:00"),
        ("08:31:01", "11:01:00"),
        ("11:01:01", "13:31:00"),
        ("13:31:01", "15:34:00"),
        ("15:34:01", "23:59:59"),
    ]
    DEPOSIT_SLOTS = [
        ("00:00:00", "10:30:00"),
        ("10:30:01", "13:00:00"),
        ("13:00:01", "15:30:00"),
        ("15:30:01", "17:30:00"),
        ("17:30:01", "23:59:59"),
    ]
    
class AchConstants:
    """Constants used in ach processing."""
    ACH_DEPOSIT_CUD = [0.0, 0.0, 0.0, 0.0, 0.0]
    SEND_RETURNS = [0.0, 0.0, 0.0, 0.0, 0.0]
    UNAUTHORIZED_STATUS = "unauthorized"
    OUT_SUFFIX = "OUT"
    SENT_REFUND_TYPE = "_ach_dev_enviada"
    CYCLE_THRESHOLD = 4
    TOTAL_CYCLES = 5

    # Column names
    NAME = "name"
    STATUS = "status"
    TRANSACTION_TYPE = "transaction_type"
    RECEIVING_ACCOUNT = "6_cuenta_receptora"
    RECEIVING_ENTITY = "6_entidad_receptora"
    ORIGINATING_NAME = "5_nombre_originador"
    ORIGINATING_ENTITY = "5_entidad_originadora"
    RECEIVING_CLIENT_NAME = "6_nombre_cliente_receptor"
    TRANSACTION_VALUE = "6_valor_transaccion"
    DATE = "fecha"


class CreditConstants:
    """Constants used in credit processing."""
    SEBRA_CONCEPTS = [
        'TRASLADO FONDOS SEBRA DEBITO', 
        'TRASLADO FONDOS SEBRA CREDITO', 
        'DEVOLUCION TRASLADO FONDOS SEBRA DEBITO', 
        'DEVOLUCION TRASLADO FONDOS SEBRA CREDITO'
    ]
    CREDIT_ACCOUNT = "12528874205"
    CONFIRMING_ACCOUNT = "12561730308"
    CREDIT_ACCOUNTS = [CREDIT_ACCOUNT, CONFIRMING_ACCOUNT]
    EXCLUDE_CONCEPTS = [
        'RECARGA SALDO PARA OPERACIONES DE CRED/CONF', 
        'DESCARGA SALDOS RECAUDOS CREDITOS'
    ]
    DEPOSIT_CROS = "DEPOSITO CROS"
    ORIGINATOR_ACCOUNT = "62015991"
        
class ExcelConstants:
    """Constants used in Excel report generation."""
    SHEET_TITLE = "Control Caja"
    HEADER_TITLE = "FECHA REPORTE"
    CURRENCY_FORMAT = '"$"#,##0.00'
    PERCENTAGE_FORMAT = '0.00"%"'
    START_ROW = 3
    HEADER_ROW = 1
    TITLE_COL = 1
    DATA_START_COL = 2
    LINE_BREAK = 1
    COLUMN_PADDING = 5
    MIN_COLUMN_WIDTH = 15
    SECTION_INCOME = "INGRESOS"
    SECTION_EXPENSE = "EGRESOS"
    SECTION_AVAILABLE_T0 = "DISPONIBLE T-0"
    SECTION_AVAILABLE_T1 = "DISPONIBLE T-1"
    SECTION_SUMMARY = "RESUMEN DISPONIBLE"
    PERCENTAGE_COLUMN = "porcentaje_diferencia"
    
DEFAULT_INPUT_DIC = [{
    "incomeComercialesCop": 0.0,
    "incomeRepos": 0.0,
    "incomeSimultaneaTES": 0.0,
    "incomeSimultaneaPrivada": 0.0,
    "incomeVentaDivisas": 0.0,
    "incomeSwapCaja": 0.0,
    "incomeCDT": 0.0,
    "incomeBonos": 0.0,
    "incomeCreditoCapital": 0.0,
    "incomeCreditoINT8ereses": 0.0,
    "incomeTIDIS": 0.0,
    "incomeTCO": 0.0,
    "incomeTDA": 0.0,
    "outcomeEncaje": 0.0,
    "outcomeComercialesCop": 0.0,
    "outcomeDepositoRemunerado": 0.0,
    "outcomeRepos": 0.0,
    "outcomeSimultaneaTES": 0.0,
    "outcomeSimultaneaPrivada": 0.0,
    "outcomeCompraDivisas": 0.0,
    "outcomeSwapCaja": 0.0,
    "outcomeRecompras": 0.0,
    "outcomeDesembolsos": 0.0,
    "outcomeTIDIS": 0.0,
    "outcomeTCO": 0.0,
    "outcomeTDA": 0.0,
    "outcomeSEBRA": 0.0,
    }, "Without registers"]

PARTITION_KEYS = ["fecha_reporte"]
MERGE_KEYS = ["fecha_reporte"]
MERGE_AVAILABLE = ["fecha_reporte", "tipo_disponible"]

