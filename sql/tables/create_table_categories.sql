/* ===================================================================================================
   Project:            	Mind cloud
   Author:             	Buldey Alexander
   Contact:             https://t.me/Alex_Booldey
   Description:         The script creates the table of categories
   Version:           	1.0
   History:           	May 25, 2018 - Created
  ===================================================================================================*/
CREATE TABLE IF NOT EXISTS categories (
	f_id 			    bigint 			  NOT NULL AUTO_INCREMENT, 	/*category id*/
	f_parent_id 	bigint 		  	NOT NULL,					        /*article id*/
	f_category 		varchar(150) 	NOT NULL,					        /*article category*/
	CONSTRAINT    categories_pk PRIMARY KEY (f_id)
);

ALTER TABLE categories ADD CONSTRAINT categories_fk FOREIGN KEY (f_parent_id) REFERENCES NEWS(f_id);
