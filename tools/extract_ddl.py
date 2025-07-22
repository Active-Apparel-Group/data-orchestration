#!/usr/bin/env python3
"""
Extract DDL for Azure SQL Tables

This script connects to Azure SQL databases and extracts DDL (Data Definition Language)
for tables, including CREATE TABLE statements, indexes, and constraints.
"""

import sys
import os
import logging
from pathlib import Path

# Clean import pattern matching working integration tests
repo_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(repo_root))

# Modern import pattern for project utilities
from pipelines.utils import db, logger
import staging_helper



# Load configuration from centralized config
config = db.load_config()

logger = logger.get_logger("extract_ddl")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_table_ddl(connection, schema_name='dbo', table_name=None):
    """
    Extract DDL for tables using T-SQL queries.
    
    Args:
        connection: Database connection
        schema_name: Schema name (default: 'dbo')
        table_name: Specific table name (optional, if None gets all tables)
    
    Returns:
        Dict containing DDL statements
    """
    cursor = connection.cursor()
    ddl_results = {}
    
    try:        
        # Get list of tables
        if table_name:
            table_filter = f"AND TABLE_NAME = '{table_name}'"
        else:
            table_filter = ""
        
        tables_query = f"""
        SELECT TABLE_SCHEMA, TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE' 
        AND TABLE_SCHEMA = '{schema_name}'
        {table_filter}
        ORDER BY TABLE_NAME
        """
        
        cursor.execute(tables_query)
        tables = cursor.fetchall()
        
        for table in tables:
            schema, table_name = table[0], table[1]
            full_table_name = f"{schema}.{table_name}"
            
            logger.info(f"Extracting DDL for {full_table_name}")
            
            # Get columns and data types
            columns_query = f"""
            SELECT 
                c.COLUMN_NAME,
                c.DATA_TYPE,
                c.CHARACTER_MAXIMUM_LENGTH,
                c.NUMERIC_PRECISION,
                c.NUMERIC_SCALE,
                c.IS_NULLABLE,
                c.COLUMN_DEFAULT,
                CASE WHEN pk.COLUMN_NAME IS NOT NULL THEN 'YES' ELSE 'NO' END AS IS_PRIMARY_KEY
            FROM INFORMATION_SCHEMA.COLUMNS c
            LEFT JOIN (
                SELECT ku.TABLE_SCHEMA, ku.TABLE_NAME, ku.COLUMN_NAME
                FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS AS tc
                INNER JOIN INFORMATION_SCHEMA.KEY_COLUMN_USAGE AS ku
                    ON tc.CONSTRAINT_TYPE = 'PRIMARY KEY' 
                    AND tc.CONSTRAINT_NAME = ku.CONSTRAINT_NAME
            ) pk ON c.TABLE_SCHEMA = pk.TABLE_SCHEMA 
                AND c.TABLE_NAME = pk.TABLE_NAME 
                AND c.COLUMN_NAME = pk.COLUMN_NAME
            WHERE c.TABLE_SCHEMA = '{schema}' AND c.TABLE_NAME = '{table_name}'
            ORDER BY c.ORDINAL_POSITION
            """
            
            cursor.execute(columns_query)
            columns = cursor.fetchall()
            
            # Build CREATE TABLE statement
            create_statement = f"CREATE TABLE [{schema}].[{table_name}] (\n"
            column_definitions = []
            primary_keys = []
            
            for col in columns:
                col_name, data_type, max_length, precision, scale, nullable, default, is_pk = col
                
                # Build column definition
                col_def = f"    [{col_name}] {data_type.upper()}"
                
                # Add length/precision
                if data_type.lower() in ['varchar', 'nvarchar', 'char', 'nchar'] and max_length:
                    if max_length == -1:
                        col_def += "(MAX)"
                    else:
                        col_def += f"({max_length})"
                elif data_type.lower() in ['decimal', 'numeric'] and precision:
                    col_def += f"({precision},{scale or 0})"
                
                # Add nullability
                if nullable == 'NO':
                    col_def += " NOT NULL"
                else:
                    col_def += " NULL"
                
                # Add default
                if default:
                    col_def += f" DEFAULT {default}"
                
                column_definitions.append(col_def)
                
                # Track primary keys
                if is_pk == 'YES':
                    primary_keys.append(col_name)
            
            create_statement += ",\n".join(column_definitions)
            
            # Add primary key constraint
            if primary_keys:
                pk_cols = ", ".join([f"[{pk}]" for pk in primary_keys])
                create_statement += f",\n    CONSTRAINT [PK_{table_name}] PRIMARY KEY ({pk_cols})"
            
            create_statement += "\n);\n"
              
            # Get indexes
            indexes_query = f"""
            SELECT 
                i.name AS index_name,
                i.is_unique,
                i.type_desc,
                STUFF((
                    SELECT ', [' + c.name + ']'
                    FROM sys.index_columns ic2
                    INNER JOIN sys.columns c ON ic2.object_id = c.object_id AND ic2.column_id = c.column_id
                    WHERE ic2.object_id = i.object_id AND ic2.index_id = i.index_id
                    ORDER BY ic2.key_ordinal
                    FOR XML PATH('')
                ), 1, 2, '') AS columns
            FROM sys.indexes i
            INNER JOIN sys.tables t ON i.object_id = t.object_id
            INNER JOIN sys.schemas s ON t.schema_id = s.schema_id
            WHERE s.name = '{schema}' 
            AND t.name = '{table_name}'
            AND i.is_primary_key = 0  -- Exclude primary key
            AND i.type > 0  -- Exclude heaps
            AND i.name IS NOT NULL
            ORDER BY i.name
            """
            
            cursor.execute(indexes_query)
            indexes = cursor.fetchall()
            
            index_statements = []
            for idx in indexes:
                idx_name, is_unique, type_desc, columns = idx
                unique_clause = "UNIQUE " if is_unique else ""
                index_stmt = f"CREATE {unique_clause}INDEX [{idx_name}] ON [{schema}].[{table_name}] ({columns});"
                index_statements.append(index_stmt)
            
            # Store results
            ddl_results[full_table_name] = {
                'create_table': create_statement,
                'indexes': index_statements
            }
            
    except Exception as e:
        logger.error(f"Error extracting DDL: {e}")
        raise
    finally:
        cursor.close()
    
    return ddl_results

def extract_ddl_for_database(db_key, output_dir, schema_name='dbo', table_name=None, save_to_source=False):
    """
    Extract DDL for all tables in a database and save to files.
    
    Args:
        db_key: Database key from config (e.g., 'DMS', 'ORDERS')
        output_dir: Directory to save DDL files
        schema_name: Schema name (default: 'dbo')
        table_name: Specific table name (optional)
        save_to_source: If True, also save organized DDL to db/ddl/ directory
    """
    logger.info(f"Extracting DDL for database: {db_key}")
    
    try:
        with db.get_connection(db_key) as conn:
            ddl_results = get_table_ddl(conn, schema_name, table_name)
              
            # Create output directory
            output_path = Path(output_dir) / db_key.lower()
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Also create organized source DDL directory if requested
            if save_to_source:
                source_ddl_path = Path(__file__).parent.parent / "db" / "ddl" / "tables" / db_key.lower()
                source_ddl_path.mkdir(parents=True, exist_ok=True)
            
            # Save each table's DDL
            for table_full_name, ddl_info in ddl_results.items():
                # Output file (artifacts)
                table_file = output_path / f"{table_full_name.replace('.', '_')}_ddl.sql"
                
                # Source control file (organized DDL)
                if save_to_source:
                    clean_table_name = table_full_name.replace('.', '_').lower()
                    source_table_file = source_ddl_path / f"{clean_table_name}.sql"
                
                # Write main output file
                with open(table_file, 'w', encoding='utf-8') as f:
                    f.write(f"-- DDL for {table_full_name}\n")
                    f.write(f"-- Generated from database: {db_key}\n")
                    f.write(f"-- Schema: {schema_name}\n")
                    f.write(f"-- Generated on: {Path(__file__).parent.parent.name} project\n\n")
                    
                    # Write CREATE TABLE
                    f.write("-- CREATE TABLE Statement\n")
                    f.write(ddl_info['create_table'])
                    f.write("\n")
                    
                    # Write indexes
                    if ddl_info['indexes']:
                        f.write("-- Indexes\n")
                        for idx_stmt in ddl_info['indexes']:
                            f.write(f"{idx_stmt}\n")
                        f.write("\n")
                
                # Write organized source file if requested
                if save_to_source:
                    with open(source_table_file, 'w', encoding='utf-8') as f:
                        f.write(f"-- Table: {table_full_name}\n")
                        f.write(f"-- Database: {db_key}\n")
                        f.write(f"-- Purpose: [Add description of table purpose]\n")
                        f.write(f"-- Dependencies: [List any dependent tables/views]\n\n")
                        
                        # Clean CREATE TABLE (remove generated comments)
                        f.write(ddl_info['create_table'])
                        
                        if ddl_info['indexes']:
                            f.write("\n-- Indexes\n")
                            for idx_stmt in ddl_info['indexes']:
                                f.write(f"{idx_stmt}\n")
                
                logger.info(f"Saved DDL to: {table_file}")
                if save_to_source:
                    logger.info(f"Saved source DDL to: {source_table_file}")
            
            return len(ddl_results)
            
    except Exception as e:
        logger.error(f"Failed to extract DDL for {db_key}: {e}")
        raise

def main():
    """Main function to extract DDL from configured databases."""
    
    # Output directory for DDL files
    output_dir = Path(__file__).parent.parent / "outputs" / "ddl"
    
    # Available databases from your config
    databases = ['DMS', 'ORDERS', 'DISTRIBUTION', 'WAH', 'QUICKDATA']
    
    print("🔧 Azure SQL DDL Extraction Tool")
    print("=" * 50)
    
    # Let user choose database
    print("\nAvailable databases:")
    for i, db in enumerate(databases, 1):
        print(f"{i}. {db}")
    
    choice = input("\nSelect database (number) or 'all' for all databases: ").strip().lower()
    
    if choice == 'all':
        selected_dbs = databases
    else:
        try:
            db_index = int(choice) - 1
            if 0 <= db_index < len(databases):
                selected_dbs = [databases[db_index]]
            else:
                print("Invalid selection!")
                return
        except ValueError:
            print("Invalid input!")
            return
    
    # Optional: specific table
    table_name = input("\nEnter specific table name (or press Enter for all tables): ").strip()
    if not table_name:
        table_name = None
    
    # Optional: schema name
    schema_name = input("\nEnter schema name (default: dbo): ").strip() or 'dbo'
      
    # Optional: save to source control
    save_to_source = input("\nSave organized DDL to source control (db/ddl/)? (y/N): ").strip().lower() == 'y'
    
    total_tables = 0
    
    for db_key in selected_dbs:
        try:
            count = extract_ddl_for_database(db_key, output_dir, schema_name, table_name, save_to_source)
            total_tables += count
            print(f"✅ {db_key}: Extracted DDL for {count} tables")
        except Exception as e:
            print(f"❌ {db_key}: Failed - {e}")
    
    print(f"\n🎉 Complete! Extracted DDL for {total_tables} tables")
    print(f"📁 Output files saved to: {output_dir.absolute()}")
    if save_to_source:
        print(f"📁 Source DDL saved to: {Path(__file__).parent.parent / 'db' / 'ddl'}")
    
    # Provide guidance
    print(f"\n💡 Next Steps:")
    print(f"   1. Review generated DDL files")
    print(f"   2. Add table descriptions and dependencies")
    if save_to_source:
        print(f"   3. Commit source DDL files to version control")
        print(f"   4. Use db/ddl/ files for schema documentation")

if __name__ == "__main__":
    main()
