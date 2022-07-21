-- POST /pipelines 요청에 입력된 build specification
 CREATE TABLE `pipeline` (
  `id` INT(11) NOT NULL AUTO_INCREMENT,

   -- raw 를 deserialize 하지 않고 사용할만한 데이터
  `env` VARCHAR(16) NOT NULL COMMENT "dev|qa|stg|prod",
  `key` VARCHAR(32) NOT NULL COMMENT "Bitbucket key",
  `slug` VARCHAR(64) NOT NULL COMMENT "Bitbucket slug",
  `repository` VARCHAR(128) COMMENT "repository url",

  -- 자세한건 raw deserialize 해서 봐야 한다.
  `raw` JSON COMMENT "raw data serialized json format",
  `create_dt` DATETIME DEFAULT CURRENT_TIMESTAMP,
  `update_dt` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY(id),
  UNIQUE KEY `unique_env_key_slug` (`env`, `key`, `slug`)
) CHARACTER SET utf8 COLLATE utf8_general_ci;
