
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
    img_blob BLOB,
    his_id INT NOT NULL,
    insert_date DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (his_id , session_id , epoch_nr)
        REFERENCES its_epoch_history (id , session_id , epoch_nr),
    PRIMARY KEY (id , session_id , epoch_nr)
);


INSERT INTO its_session(
    session_id,
    max_epoch,
    info_text,
    cnt_base_imgs,
    enable_img_gen,
    cnt_gen_imgs
)
VALUES (
    0,
    0,
    'Epoche 0 ist eine Debug Epoche. Hier werden alle Testläufe gesammelt.',
    0,
    FALSE,
    0
);

INSERT INTO its_epoch_history (
    session_id,
    epoch_nr,
    disc_loss,
    gen_loss,
    disc_real_loss,
    disc_fake_loss,
    entry_id
)
VALUES (
    0,
    0,
    0,
    0,
    0,
    0,
    1
);

INSERT INTO its_request_history (
    session_id,
    epoch_nr,
    class,
    max_confidence,
    json_result,
    img_blob,
    his_id
)
VALUES (
    0,
    0,
    'dummy',
    0,
    '-1',
    NULL,
    1
);
