#!/bin/bash

#===================================================================================================
#   Project:            Mind cloud
#   Author:             Buldey Alexander
#   Contact:            https://t.me/Alex_Booldey
#   Description:        The script creates the tables articles, history, categories
#   Version:           	1.0
#   History:          	May 25, 2018 - Created
#===================================================================================================

user_name=$1
user_pass=$2
db_name=$3 

if  [ -n "$1" ] | [ -n "$2" ] | [ -n "$3" ] 
then
mysql --user=${user_name} --password=${user_pass} ${db_name} < create_procedures_wiki.sql
else
echo "ERROR parameters!"
echo "Example >create_wiki_procedures.sh [user_name] [user pass] [db_name]"
fi

