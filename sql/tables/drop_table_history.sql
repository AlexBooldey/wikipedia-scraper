/* ===================================================================================================
   Project:            	Mind cloud
   Author:             	Buldey Alexander
   Contact:             https://t.me/Alex_Booldey
   Description:         The script drop the table of history
   Version:           	1.0
   History:          	May 23, 2018 - Created
  ===================================================================================================*/
  ALTER TABLE history DROP FOREIGN KEY history_fk;
  DROP TABLE IF EXISTS history;