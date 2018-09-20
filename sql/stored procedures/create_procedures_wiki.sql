/* ===================================================================================================
   Project:            	Mind cloud
   Author:             	Buldey Alexander
   Contact:             https://t.me/Alex_Booldey
   Description:         The script creates the stored procedure
   Version:           	1.0
   History:          	May 25, 2018 - Created
  ===================================================================================================*/

DELIMITER $$
create procedure add_article(
  in p_title            varchar(1000), in p_url varchar(255), in p_author varchar(80),
  in p_publication_date datetime, in p_content text(60000), in p_language varchar(12), in p_hash char(32)) language sql
  begin
    insert into NEWS (f_Title, f_LinkToNews, f_Category, f_PublicationDate, f_Author, f_Source, f_Fulltext, f_language, f_hash)
      value
      (p_title, p_url, 'wikipedia', p_publication_date, p_author, 'https://www.wikipedia.org', p_content, p_language, p_hash);
  end $$
DELIMITER ;

DELIMITER $$
create procedure add_article_category(in p_parent_id bigint, in p_category varchar(150)) language sql
  begin
    insert into categories (f_parent_id, f_category) values (p_parent_id, p_category);
  end $$
DELIMITER ;

DELIMITER $$
create procedure add_article_history(in p_parent_id bigint, in p_date datetime, in p_user varchar(80), in p_str_date varchar(50)) language sql
  begin
    insert into history (f_parent_id, f_date, f_user, f_str_date) values (p_parent_id, p_date, p_user, p_str_date);
  end $$
DELIMITER ;

DELIMITER $$
create procedure get_id(in p_title varchar(1000)) language sql
  begin
    select f_id from NEWS where f_Title = p_title;
  end $$
DELIMITER ;

DELIMITER $$
create procedure check_exists(in p_hash char(32))language sql
	begin
		select exists(select 1 from NEWS where f_Category='wikipedia' and f_hash=p_hash);
    end $$
DELIMITER ;
