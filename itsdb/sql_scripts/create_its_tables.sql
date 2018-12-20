DROP TABLE IF EXISTS its_request_history;
DROP TABLE IF EXISTS its_epoch_history;
DROP TABLE IF EXISTS its_session;

CREATE TABLE its_session
(
    id INT NOT NULL AUTO_INCREMENT,
    session_id INT NOT NULL,
    max_epoch INT,
    info_text TEXT,
    cnt_base_imgs INT,
    enable_img_gen BOOL,
    cnt_gen_imgs INT,
    insert_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id, session_id)
);

CREATE TABLE its_epoch_history (
    id INT NOT NULL AUTO_INCREMENT,
    session_id INT NOT NULL,
    epoch_nr INT NOT NULL,
    disc_loss FLOAT,
    gen_loss FLOAT,
    disc_real_loss FLOAT,
    disc_fake_loss FLOAT,
    entry_id INT NOT NULL,
    insert_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (entry_id , session_id)
        REFERENCES its_session (id , session_id),
    PRIMARY KEY (id, session_id , epoch_nr)
);

CREATE TABLE its_request_history (
    id INT NOT NULL AUTO_INCREMENT,
    session_id INT NOT NULL,
    epoch_nr INT NOT NULL,
    class TEXT,
    max_confidence FLOAT,
    json_result TEXT,
    img_array TEXT,
    dtype_img TEXT,
    his_id INT NOT NULL,
    insert_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (his_id , session_id , epoch_nr)
        REFERENCES its_epoch_history (id , session_id , epoch_nr),
    PRIMARY KEY (id , session_id , epoch_nr)
);












