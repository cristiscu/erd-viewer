Snowflake ERD Viewer
==================================================

Entity-Relationship diagram viewer for Snowflake models, with Graphviz. The script will query INFORMATION_SCHEMA and generate DOT Graphviz models and HTML files in the output/ folder.

**Features**

* Generates HTML and DOT files for the full and simplified model, with and without column data types.  
* Also generates files for table relationships only, with no columns.  
* Generates an SQL schema creation script.
* Tables with their columns.  
* Column data type conversions, nullable, identity.  
* PK and UNIQUE constraints, for single/multiple columns, on single/separate line.  
* FK constraints, with ALTER TABLE after all created.  
* Case sensitive table and column names.  

**Limitations**

* Loads only one database schema.  
* Relationships must be within the same schema.  
* Cannot say if a table is TRANSIENT or TEMPORARY.  
* No CASCADE DELETE/UPDATE.  
* No other database objects yet (roles, users, views...).  

# Database Profile File

Create a **profiles_db.conf** copy of the **profiles_db_template.conf** file, and customize it with your own Snowflake connection parameters. Your top [default] profile is the active profile, considered by our tool. Below you may define other personal profiles, that you may override under [default] each time you want to change your active connection.

We connect to Snowflake with the Snowflake Connector for Python. We have code for (a) password-based connection, (b) connecting with a Key Pair, and (c) connecting with SSO. For password-based connection, save your password in a SNOWFLAKE_PASSWORD local environment variable. Never add the password or any other sensitive information to your code or to profile files. All names must be case sensitive, with no quotes. Always provide a database and a schema.

# CLI Executable File

Without an executable, you can use the source file directly:

**<code>python erd-viewer.py</code>**  

To compile into a CLI executable:

**<code>pip install pyinstaller</code>**  
**<code>pyinstaller --onefile erd-viewer.py</code>**  
**<code>dist/erd-viewer</code>**  

# Chinook Sample Database

Chinook is a open-source sample database schema [originally implemented by Luis Rocha](https://github.com/lerocha/chinook-database). I adapted the DDL create scripts for Snowflake, and skipped the data, as we need just the model, with the FK-based relationships.

Copy the content of the **chinook-create-database.sql** file into a new worksheet, and run the whole code. A new Chinook database, with a PUBLIC schema, will be created in Snowflake. Connect with this database and schema in the profile file.

An output/Chinook.PUBLIC.sql schema creation script file will be generated when you run the tool. For each of the model type below, a DOT and a HTML file with the -full, -columns, and -relationship suffix will also be generated in the output/ folder. We saved static samples in the images/ folder, for demo purposes.

You may copy and paste the content of the DOT files in a free online Graphiz viewer like [http://viz-js.com](http://viz-js.com). But it is more convenient to look directly at the HTML files in your browser, because we used a [D3 Graphviz renderer](https://github.com/magjac/d3-graphviz#creating-a-graphviz-renderer) that automatically shows the generated SVGs.

**Full Model**

The full model shows all table shapes expanded, with column names and their data types. PKs are underlined, FKs are in italic, and columns that accept NULLs get a special character suffix. Dashed arrows connect FK-based relationships that may have NULL FK values:

![Full Model](/images/Chinook.PUBLIC-full.png)

**Columns Model**

The columns model shows all table shapes expanded, with just column names (no data types):

![Columns Model](/images/Chinook.PUBLIC-columns.png)

**Relationships Model**

The relationships model shows all table shapes collapsed, with no columns:

![Relationships Model](/images/Chinook.PUBLIC-relationships.png)

# Built-in Themes

We have five built-in themes, that you may pass as "theme" in the profile file (they are case sensitive, do not omit and do not add more spaces). By default this is **"Common Gray"**, but other acceptable values are **"Blue Navy"**, **"Gradient Green"**, **"Blue Sky"**, and **"Common Gray Box"**. Here are column-based models with other different themes.

**Blue Navy Theme**

![Full Model](/images/Chinook.PUBLIC-columns-BN.png)

**Gradient Green Theme**

![Full Model](/images/Chinook.PUBLIC-columns-GG.png)

**Blue Sky Theme**

![Full Model](/images/Chinook.PUBLIC-columns-BS.png)

**Common Gray Box Theme**

![Full Model](/images/Chinook.PUBLIC-columns-CGB.png)
