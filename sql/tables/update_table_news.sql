/* ===================================================================================================
   Project:            	Mind cloud
   Author:             	Buldey Alexander
   Contact:             https://t.me/Alex_Booldey
   Description:         The script creates the table of categories
   Version:           	1.1
   History:           	May 25, 2018 - Created
                        May 29, 2018 - Add columns f_language, f_hash
  ===================================================================================================*/

ALTER TABLE NEWS
  ADD f_language varchar(12),
  ADD f_hash char(32);
