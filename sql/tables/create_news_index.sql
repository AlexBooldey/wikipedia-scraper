CREATE UNIQUE index i_hash ON NEWS (f_hash) USING btree;
CREATE index i_category ON NEWS (f_category) USING btree;