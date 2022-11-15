CREATE TABLE android_metadata (locale TEXT);

CREATE TABLE ITEMTABLE(
    itemTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    itemName VARCHAR(63),
    itemAutoFillVisibility INTEGER
);

CREATE TABLE sqlite_sequence(name, seq);

CREATE TABLE CHILDCATEGORYTABLE(
    categoryTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    childCategoryName VARCHAR(63),
    parentCategoryID INTEGER,
    budgetAmount INTEGER,
    budgetCustomSetup VARCHAR(255),
    budgetPeriod INTEGER,
    budgetEnabledCategoryChild INTEGER,
    childCategoryIcon VARCHAR(255),
    categorySelectorVisibility INTEGER,
    categoryExtraColumnInt1 INTEGER,
    categoryExtraColumnInt2 INTEGER,
    categoryExtraColumnString1 VARCHAR(255),
    categoryExtraColumnString2 VARCHAR(255)
);

CREATE INDEX 'categoryChildTable1' ON CHILDCATEGORYTABLE(parentCategoryID);

CREATE TABLE PARENTCATEGORYTABLE(
    parentCategoryTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    parentCategoryName VARCHAR(63),
    categoryGroupID INTEGER,
    budgetAmountCategoryParent INTEGER,
    budgetCustomSetupParent VARCHAR(255),
    budgetPeriodCategoryParent INTEGER,
    budgetEnabledCategoryParent INTEGER,
    categoryParentExtraColumnInt1 INTEGER,
    categoryParentExtraColumnInt2 INTEGER,
    categoryParentExtraColumnString1 VARCHAR(255),
    categoryParentExtraColumnString2 VARCHAR(255)
);

CREATE INDEX 'categoryParentTable1' ON PARENTCATEGORYTABLE(categoryGroupID);

CREATE TABLE ACCOUNTSTABLE(
    accountsTableID INTEGER PRIMARY KEY,
    accountName VARCHAR(63),
    accountTypeID INTEGER,
    accountHidden INTEGER,
    accountCurrency VARCHAR(5),
    accountConversionRateNew REAL,
    currencyChanged INTEGER,
    creditLimit INTEGER,
    cutOffDa INTEGER,
    creditCardDueDate INTEGER,
    cashBasedAccounts INTEGER,
    accountSelectorVisibility INTEGER,
    accountsExtraColumnInt1 INTEGER,
    accountsExtraColumnInt2 INTEGER,
    accountsExtraColumnString1 VARCHAR(255),
    accountsExtraColumnString2 VARCHAR(255)
);

CREATE INDEX 'accountsTable1' ON ACCOUNTSTABLE(accountTypeID);

CREATE TABLE ACCOUNTTYPETABLE(
    accountTypeTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    accountTypeName VARCHAR(255),
    accountingGroupID INTEGER
);

CREATE INDEX 'accountsTypeTable1' ON ACCOUNTTYPETABLE(accountingGroupID);

CREATE TABLE ACCOUNTINGGROUPTABLE(
    accountingGroupTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    accountGroupName VARCHAR(15)
);

CREATE TABLE TRANSACTIONTYPETABLE(
    transactionTypeTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    transactionTypeName VARCHAR(7)
);

CREATE TABLE TRANSACTIONSTABLE(
    transactionsTableID INTEGER PRIMARY KEY,
    itemID INTEGER,
    amount INTEGER,
    transactionCurrency VARCHAR(5),
    conversionRateNew REAL,
    date DATETIME DEFAULT CURRENT_TIMESTAMP,
    transactionTypeID INTEGER,
    categoryID INTEGER,
    accountID INTEGER,
    notes VARCHAR(255),
    status INTEGER,
    accountReference INTEGER,
    accountPairID INTEGER,
    uidPairID INTEGER,
    deletedTransaction INTEGER,
    newSplitTransactionID INTEGER,
    transferGroupID INTEGER,
    hasPhoto INTEGER,
    labelCount INTEGER,
    reminderTransaction INTEGER,
    reminderGroupID INTEGER,
    reminderFrequency INTEGER,
    reminderRepeatEvery INTEGER,
    reminderEndingType INTEGER,
    reminderStartDate DATETIME,
    reminderEndDate DATETIME,
    reminderAfterNoOfOccurences INTEGER,
    reminderAutomaticLogTransaction INTEGER,
    reminderRepeatByDayOfMonth INTEGER,
    reminderExcludeWeekend INTEGER,
    reminderWeekDayMoveSetting INTEGER,
    reminderUnbilled INTEGER,
    creditCardInstallment INTEGER,
    reminderVersion INTEGER,
    dataExtraColumnString1 VARCHAR(255)
);

CREATE INDEX 'transactionsTable1' ON TRANSACTIONSTABLE(accountID);

CREATE INDEX 'transactionsTable2' ON TRANSACTIONSTABLE(categoryID);

CREATE TABLE CATEGORYGROUPTABLE(
    categoryGroupTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    categoryGroupName VARCHAR(63)
);

CREATE TABLE PICTURETABLE(
    pictureTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    pictureFileName VARCHAR(63),
    transactionID INTEGER
);

CREATE TABLE LABELSTABLE(
    labelsTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    labelName VARCHAR(63),
    transactionIDLabels INTEGER
);

CREATE TABLE SETTINGSTABLE(
    settingsTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    defaultSettings VARCHAR(40)
);

CREATE TABLE SMSSTABLE(
    smsTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    senderName VARCHAR(63),
    senderDefaultName VARCHAR(63),
    senderCategoryID INTEGER,
    senderAccountID INTEGER,
    senderAmountOrder INTEGER
);

CREATE TABLE FILTERSTABLE(
    filtersTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    filtername VARCHAR(255),
    filterJSON VARCHAR(255)
);

CREATE TABLE NOTIFICATIONTABLE(
    smsTableID INTEGER PRIMARY KEY AUTOINCREMENT,
    notificationPackageName VARCHAR(255),
    notificationAppName VARCHAR(255),
    notificationDefaultName VARCHAR(255),
    notificationSenderCategoryID INTEGER,
    notificationSenderAccountID INTEGER,
    notificationSenderAmountOrder INTEGER
);