/* ===================================================================================================
   Project:            	Mind cloud
   Author:             	Buldey Alexander
   Contact:             https://t.me/Alex_Booldey
   Description:         The script create index i_hash and i_category in table NEWS
   Version:           	1.0
   History:           	June 24, 2018 - Created
  ===================================================================================================*/
create unique index i_hash on NEWS (f_hash) using btree;
create index i_category on NEWS (f_category) using btree;