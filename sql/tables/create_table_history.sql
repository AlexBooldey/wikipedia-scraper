/* ===================================================================================================
   Project:            	Mind cloud
   Author:             	Buldey Alexander
   Contact:             https://t.me/Alex_Booldey
   Description:         The script creates the table of history
   Version:           	1.0
   History:          	  May 25, 2018 - Created
  ===================================================================================================*/
CREATE TABLE IF NOT EXISTS history (
	f_id 			    bigint		NOT NULL AUTO_INCREMENT,	/*history id*/
	f_parent_id 	bigint 		NOT NULL,					        /*article category*/
	f_date 			  datetime,								            /*the date of the article change*/
	f_user 			  varchar(80),			                  /*who changed the article*/
	f_str_date    varchar(50),                        /*the date format str (unsupported)*/
	CONSTRAINT history_pk PRIMARY KEY (f_id)
);

ALTER TABLE history ADD CONSTRAINT history_fk FOREIGN KEY (f_parent_id) REFERENCES NEWS(f_id);

