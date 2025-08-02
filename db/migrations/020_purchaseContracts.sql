CREATE TABLE Contracts (
    ContractID      INT IDENTITY(1,1) PRIMARY KEY,
    ContractNo      NVARCHAR(64) NOT NULL,
    OrderDate       DATE NOT NULL,
    JsonPayload     NVARCHAR(MAX) NOT NULL,
    CreatedAt       DATETIME2 DEFAULT SYSUTCDATETIME()
);
