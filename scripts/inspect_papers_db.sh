#!/bin/bash

# Path to the SQLite database file
DBFILE="_bibliography/gscholar_export.db"

# Check if the database file exists
if [[ ! -f "$DBFILE" ]]; then
  echo "Error: Database file '$DBFILE' not found."
  exit 1
fi

echo "=================================="
echo "SQLite DB Status Report"
echo "Database: $DBFILE"
echo "=================================="
echo ""

# Print the list of tables
echo "-> Tables in database:"
sqlite3 "$DBFILE" ".tables"
echo ""

# Print the schema for the publications table
echo "-> Schema for 'publications' table:"
sqlite3 "$DBFILE" ".schema publications"
echo ""

# Print the total number of records in the publications table
echo "-> Total number of records in 'publications' table:"
sqlite3 "$DBFILE" "SELECT COUNT(*) FROM publications;"
echo ""

# Print an example row from the publications table
echo "-> Example rows from 'publications' table:"
sqlite3 "$DBFILE" <<EOF
.mode column
.headers on
SELECT * FROM publications LIMIT 5;
EOF
echo ""

