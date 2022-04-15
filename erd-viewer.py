"""
Created By:    Cristian Scutaru
Creation Date: Nov 2021
Company:       XtractPro Software
"""

import os, sys, re, json
import argparse
import configparser
import snowflake.connector
from pathlib import Path
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

def getName(name):
    return name.lower() if re.match("^[A-Z_0-9]*$", name) != None else f'"{name}"'

class Table:
    """
    Database table, with columns, primary keys and foreign keys, as constraints
    """
    
    def __init__(self, name, comment):
        self.name = name
        self.comment = comment
        self.label = None

        self.columns = []           # list of all columns
        self.uniques = {}           # dictionary with UNIQUE constraints, by name + list of columns
        self.pks = []               # list of PK columns (if any)
        self.fks = {}               # dictionary with FK constraints, by name + list of FK columns

    def getColumn(self, name):
        for column in self.columns:
            if column.name == name:
                return column
        return None

    def getUniques(self, name):
        constraint = self.uniques[name]
        uniques = [getName(column.name) for column in constraint]
        ulist = ", ".join(uniques)
        return f",\n  unique ({ulist})"

    def getPKs(self):
        pks = [getName(column.name) for column in self.pks]
        pklist = ", ".join(pks)
        return f",\n  primary key ({pklist})"

    def getFKs(self, name):
        constraint = self.fks[name]
        pktable = constraint[0].fkof.table

        fks = [getName(column.name) for column in constraint]
        fklist = ", ".join(fks)
        pks = [getName(column.fkof.name) for column in constraint]
        pklist = ", ".join(pks)
        return (f"alter table {getName(self.name)}\n"
            + f"  add foreign key ({fklist}) references {getName(pktable.name)} ({pklist});\n\n")

    # outputs a CREATE TABLE statement for the current table
    def getCreateTable(self):
        s = f"create or replace table {getName(self.name)} ("
        
        first = True
        for column in self.columns:
            if first: first = False
            else: s += ","
            s += column.getCreateColumn()

        if len(self.uniques) > 0:
            for constraint in self.uniques:
                s += self.getUniques(constraint)
        if len(self.pks) >= 2:
            s += self.getPKs()
        
        s += "\n)"
        if self.comment != '':
            comment = self.comment.replace("'", "''")
            s += f" comment = '{comment}'"
        return s + ";\n\n"

    def getDotShape(self, theme, isFull, isCollapsed):
        color = fillcolor = bgcolor = "transparent"
        icolor = tcolor = "#000000"
        style = "rounded"
        if theme == "Common Gray" or theme == "Common Gray Box":
            color = "#6c6c6c"
            bgcolor = "#e0e0e0"
            fillcolor = "#f5f5f5" if not isCollapsed else bgcolor
        elif theme == "Blue Navy":
            color = "#1a5282"
            bgcolor = "#1a5282"
            fillcolor = "#ffffff" if not isCollapsed else bgcolor
            tcolor = "#ffffff"
        elif theme == "Gradient Green":
            color = "#716f64"
            bgcolor = "transparent"
            fillcolor = "#008080:#ffffff"
        elif theme == "Blue Sky":
            color = "#716f64"
            bgcolor = "transparent"
            fillcolor = "#d3dcef:#ffffff"

        colspan = "2" if isFull else "1"
        s = (f'  {self.label} [\n'
            + f'    fillcolor="{fillcolor}" color="{color}" penwidth="1"\n'
            + f'    label=<<table style="{style}" border="0" cellborder="0" cellspacing="0" cellpadding="1">\n'
            + f'      <tr><td bgcolor="{bgcolor}" align="center" colspan="{colspan}"><font color="{tcolor}"><b>{self.name}</b></font></td></tr>\n')

        if isFull or not isCollapsed:
            for column in self.columns:
                name = column.name
                if column.ispk: name = f"<u>{name}</u>"
                if column.fkof != None: name = f"<i>{name}</i>"
                if column.nullable: name = f"{name}*"
                if column.identity: name = f"{name} I"
                if column.isunique: name = f"{name} U"

                if isFull:
                    s += (f'      <tr><td align="left"><font color="{icolor}">{name}&nbsp;</font></td>\n'
                        + f'        <td align="left"><font color="{icolor}">{column.datatype}</font></td></tr>\n')
                else:
                    s += f'      <tr><td align="left"><font color="{icolor}">{name}</font></td></tr>\n'

        return s + '    </table>>\n  ]\n'

    def getDotLinks(self, theme):
        pencolor = "#696969"
        penwidth = "1"
        if theme == "Blue Navy":
            pencolor = "#0078d7"
            penwidth = "2"

        s = ""
        for constraint in self.fks:
            fks = self.fks[constraint]
            fk1 = fks[0]
            dashed = "" if not fk1.nullable else ' style="dashed"'
            arrow = "" if fk1.ispk and len(self.pks) == len(fk1.fkof.table.pks) else ' arrowtail="crow"'
            s += f'  {self.label} -> {fk1.fkof.table.label} [ penwidth="{penwidth}" color="{pencolor}"{dashed}{arrow} ]\n'
        return s

class Column:
    """
    Database table column, with data type, nullable, identity, FK of
    """
    
    def __init__(self, table, name, comment):
        self.table = table
        self.name = name
        self.comment = comment
        self.nullable = True
        self.datatype = None        # with (length, or precision/scale)
        self.identity = False

        self.isunique = False
        self.ispk = False
        self.fkof = None            # points to the PK column on the other side

    # outputs the column definition in a CREATE TABLE statement, for the parent table
    def getCreateColumn(self):
        nullable = "" if self.nullable or (self.ispk and len(self.table.pks) == 1) else " not null"
        identity = "" if not self.identity else " identity"
        pk = "" if not self.ispk or len(self.table.pks) >= 2 else " primary key"
        
        comment = self.comment.replace("'", "''")
        if comment != '':
            comment = f" comment '{comment}'"

        return f"\n  {getName(self.name)} {self.datatype}{nullable}{identity}{pk}{comment}"

def importMetadata(tables, cur):
    """
    Loads info about tables and relationships from a Snowflake database schema.
    """

    # get tables
    results = cur.execute("show tables").fetchall()
    for row in results:
        name = str(row[1])
        table = Table(name, str(row[5]))
        tables[name] = table
        table.label = f"n{len(tables)}"

    # get table columns
    results = cur.execute("show columns").fetchall()
    for row in results:
        name = str(row[2])
        table = tables[str(row[0])]
        column = Column(table, name, str(row[8]))
        table.columns.append(column)
        column.identity = str(row[10]) != ''

        # get and convert column data type
        datatype = json.loads(str(row[3]))
        column.datatype = datatype["type"]
        column.nullable = bool(datatype["nullable"])

        if column.datatype == "FIXED":
            column.datatype = "NUMBER"
        elif "fixed" in datatype:
            fixed = bool(datatype["fixed"])
            if column.datatype == "TEXT":
                column.datatype = "CHAR" if fixed else "VARCHAR"

        if "length" in datatype:
            column.datatype += f"({str(datatype['length'])})"
        elif "scale" in datatype:
            if int(datatype['precision']) == 0:
                column.datatype += f"({str(datatype['scale'])})"
                if column.datatype == "TIMESTAMP_NTZ(9)":
                    column.datatype = "TIMESTAMP"
            elif "scale" in datatype and int(datatype['scale']) == 0:
                column.datatype += f"({str(datatype['precision'])})"
                if column.datatype == "NUMBER(38)":
                    column.datatype = "INT"
                elif column.datatype.startswith("NUMBER("):
                    column.datatype = f"INT({str(datatype['precision'])})"
            elif "scale" in datatype:
                column.datatype += f"({str(datatype['precision'])},{str(datatype['scale'])})"
                #if column.datatype.startswith("NUMBER("):
                #    column.datatype = f"FLOAT({str(datatype['precision'])},{str(datatype['scale'])})"
        column.datatype = column.datatype.lower()
        
    # get UNIQUE constraints
    results = cur.execute("show unique keys").fetchall()
    for row in results:
        table = tables[str(row[3])]
        column = table.getColumn(str(row[4]))

        # add a UNIQUE constraint (if not there) with the current column
        constraint = str(row[6])
        if constraint not in table.uniques:
            table.uniques[constraint] = []
        table.uniques[constraint].append(column)
        column.isunique = True

    # get PKs
    results = cur.execute("show primary keys").fetchall()
    for row in results:
        table = tables[str(row[3])]
        column = table.getColumn(str(row[4]))
        column.ispk = True

        pos = int(row[5]) - 1
        table.pks.insert(pos, column)

    # get FKs
    results = cur.execute("show imported keys").fetchall()
    for row in results:
        pktable = tables[str(row[3])]
        pkcolumn = pktable.getColumn(str(row[4]))
        fktable = tables[str(row[7])]
        fkcolumn = fktable.getColumn(str(row[8]))

        if str(row[2]) != str(row[6]):
            print(f"??? Relationship accross schemas, for {fktable.name}.{fkcolumn.name}!")
        else:
            # add a constraint (if not there) with the current FK column
            constraint = str(row[12])
            if constraint not in fktable.fks:
                fktable.fks[constraint] = []
            fktable.fks[constraint].append(fkcolumn)

            fkcolumn.fkof = pkcolumn
            #print(f"{fktable.name}.{fkcolumn.name} -> {pktable.name}.{pkcolumn.name}")

def dumpCreateScript(s, tables, filename):
    """
    Dump all, as CREATE TABLE statements, on screen and to SQL script file
    """

    s += ";\n\n"
    for name in tables:
        s += tables[name].getCreateTable()
    for name in tables:
        for constraint in tables[name].fks:
            s += tables[name].getFKs(constraint)
    print(s)

    with open(filename, "w") as file:
        file.write(s)

def dumpDotERD(tables, theme, filename):
    """
    Dump all, as GraphViz ERD, on screen and to DOT file
    """

    isCollapsed = filename.endswith("-relationships")
    isFull = filename.endswith("-full") 

    shape = "Mrecord"
    if " Box" in theme:
        shape = "record"

    s = ('# You may copy and paste all this to http://viz-js.com/\n\n'
        + 'digraph G {\n'
        + '  graph [ rankdir="LR" bgcolor="#ffffff" ]\n'
        + f'  node [ style="filled" shape="{shape}" gradientangle="180" ]\n'
        + '  edge [ arrowhead="none" arrowtail="none" dir="both" ]\n\n')

    for name in tables:
        s += tables[name].getDotShape(theme, isFull, isCollapsed)
    s += "\n"
    for name in tables:
        s += tables[name].getDotLinks(theme)
    s += "}\n"
    print(s)

    # save as DOT file
    with open(f"{filename}.dot", "w") as file:
        file.write(s)

    # with d3-graphviz
    # https://bl.ocks.org/magjac/4acffdb3afbc4f71b448a210b5060bca
    # https://github.com/magjac/d3-graphviz#creating-a-graphviz-renderer
    s = ('<!DOCTYPE html><html>\n'
        + '<head><meta charset="utf-8"></head>\n'
        + '<body>'
        + '<script src="https://d3js.org/d3.v5.min.js"></script>\n'
        + '<script src="https://unpkg.com/@hpcc-js/wasm@0.3.11/dist/index.min.js"></script>\n'
        + '<script src="https://unpkg.com/d3-graphviz@3.0.5/build/d3-graphviz.js"></script>\n'
        + '<div id="graph" style="text-align: center;"></div>\n'
        + '<script>\n'
        + 'var graphviz = d3.select("#graph").graphviz()\n'
        + '   .on("initEnd", () => { graphviz.renderDot(d3.select("#digraph").text()); });\n'
        + '</script>\n'
        + '<textarea id="digraph" style="display:none; height:0px;">\n'
        + s
        + '</textarea></body></html>')

    # save as HTML file
    with open(f"{filename}.html", "w") as file:
        file.write(s)

def connect(connect_mode, account, user, role, warehouse, database, schema):
    # (a) connect to Snowflake with SSO
    if connect_mode == "SSO":
        return snowflake.connector.connect(
            account = account,
            user = user,
            role = role,
            database = database,
            schema = schema,
            warehouse = warehouse,
            authenticator = "externalbrowser"
        )

    # (b) connect to Snowflake with username/password
    if connect_mode == "PWD":
        return snowflake.connector.connect(
            account = account,
            user = user,
            role = role,
            database = database,
            schema = schema,
            warehouse = warehouse,
            password = os.getenv('SNOWFLAKE_PASSWORD')
        )

    # (c) connect to Snowflake with key-pair
    if connect_mode == "KEY-PAIR":
        with open(f"{str(Path.home())}/.ssh/id_rsa_snowflake_demo", "rb") as key:
            p_key= serialization.load_pem_private_key(
                key.read(),
                password = None, # os.environ['SNOWFLAKE_PASSPHRASE'].encode(),
                backend = default_backend()
            )
        pkb = p_key.private_bytes(
            encoding = serialization.Encoding.DER,
            format = serialization.PrivateFormat.PKCS8,
            encryption_algorithm = serialization.NoEncryption())

        return snowflake.connector.connect(
            account = account,
            user = user,
            role = role,
            database = database,
            schema = schema,
            warehouse = warehouse,
            private_key = pkb
        )

def main(argv):
    """
    Main entry point of the CLI
    """

    # connect to Snowflake
    parser = configparser.ConfigParser()
    parser.read("profiles_db.conf")
    section = "default"

    account = parser.get(section, "account")
    user = parser.get(section, "user")
    role = parser.get(section, "role")
    warehouse = parser.get(section, "warehouse")
    database = parser.get(section, "database")
    schema = parser.get(section, "schema")

    theme = parser.get(section, "theme", fallback="Common Gray")
    if theme not in [ "Common Gray", "Blue Navy",
        "Gradient Green", "Blue Sky", "Common Gray Box" ]:
        theme = "Common Gray"

    # change this to connect in a different way: SSO / PWD / KEY-PAIR
    connect_mode = "PWD"
    con = connect(connect_mode, account, user, role, warehouse, database, schema)
    cur = con.cursor()

    # establish context for all SHOW statements
    s = f"use schema {getName(database)}.{getName(schema)}"
    cur.execute(s)

    # load metadata
    tables = {}
    importMetadata(tables, cur)

    con.close()

    # dump all, as CREATE TABLE statements, on screen and to SQL file
    dumpCreateScript(s, tables, f"output/{database}.{schema}.sql")

    # dump all, as GraphViz ERD, on screen and to DOT file
    dumpDotERD(tables, theme, f"output/{database}.{schema}-relationships")
    dumpDotERD(tables, theme, f"output/{database}.{schema}-full")
    dumpDotERD(tables, theme, f"output/{database}.{schema}-columns")

if __name__ == "__main__":
    main('')
