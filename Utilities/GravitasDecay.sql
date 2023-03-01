/* Daily Gravitas Decay Schedule
Runs via cronjob daily at 12 pm EST
*/

/*
Decay all player's gravitas
Formula: https://i.imgur.com/jMFS3Ch.png
*/
UPDATE players
SET gravitas = gravitas - (gravitas / 5)
WHERE gravitas < 500
    AND loc NOT IN ('Aramithea', 'Riverburn', 'Thenuille');

UPDATE players
SET gravitas = gravitas + 100 - (2 * gravitas / 5)
WHERE gravitas >= 500 AND gravitas < 1000
    AND loc NOT IN ('Aramithea', 'Riverburn', 'Thenuille');

UPDATE players
SET gravitas = gravitas + 500 - (4 * gravitas / 5)
WHERE gravitas >= 1000
    AND loc NOT IN ('Aramithea', 'Riverburn', 'Thenuille');

UPDATE players
SET gravitas = gravitas - (gravitas / 10)
WHERE gravitas < 500
    AND loc IN ('Aramithea', 'Riverburn', 'Thenuille');

UPDATE players
SET gravitas = gravitas + 50 - (gravitas / 5)
WHERE gravitas >= 500 AND gravitas < 1000
    AND loc IN ('Aramithea', 'Riverburn', 'Thenuille');

UPDATE players
SET gravitas = gravitas + 650 - (4 * gravitas / 5)
WHERE gravitas >= 1000
    AND loc IN ('Aramithea', 'Riverburn', 'Thenuille');


/*
GRAVITAS PASSIVE INCOME
CLASS BONUS
    FARMER 4
    SOLDIER 1
    SCRIBE 1
*/
UPDATE players 
SET gravitas = gravitas + 4
WHERE occupation = 'Farmer';

UPDATE players
SET gravitas = gravitas + 1
WHERE occupation IN ('Soldier', 'Scribe');


/*
ORIGIN BONUS
    ARAMITHEA 5
    CITIES 3
    SOME 1
*/
UPDATE players
SET gravitas = gravitas + 5
WHERE origin = 'Aramithea';

UPDATE players
SET gravitas = gravitas + 3
WHERE origin IN ('Riverburn', 'Thenuille');

UPDATE players
SET gravitas = gravitas + 1
WHERE origin IN ('Mythic Forest', 'Lunaris', 'Crumidia');

/*
COLLEGE BONUS - 7
*/
WITH colleges AS (
    SELECT DISTINCT players.assc
    FROM players
    INNER JOIN associations
        ON players.assc = associations.assc_id
    WHERE associations.assc_type = 'College'
)
UPDATE players
SET gravitas = gravitas + 7
WHERE assc IN (SELECT assc FROM colleges);


/*
ACOLYTE BONUS: AJAR, DUCHESS
*/
WITH ajar_users AS (
    WITH acolyte1 AS (
        SELECT players.user_id, acolyte_list.effect_num[1][acolytes.copies]
        FROM players
        INNER JOIN acolytes
            ON players.acolyte1 = acolytes.acolyte_id
        INNER JOIN acolyte_list
            ON acolytes.acolyte_name = acolyte_list.name
        WHERE acolytes.acolyte_name = 'Ajar'
    ),
    acolyte2 AS (
        SELECT players.user_id, acolyte_list.effect_num[1][acolytes.copies]
        FROM players
        INNER JOIN acolytes
            ON players.acolyte2 = acolytes.acolyte_id
        INNER JOIN acolyte_list
            ON acolytes.acolyte_name = acolyte_list.name
        WHERE acolytes.acolyte_name = 'Ajar'
    )
    SELECT * FROM acolyte1
    UNION
    SELECT * FROM acolyte2
)
UPDATE players
SET gravitas = gravitas + ajar_users.effect_num
FROM ajar_users
WHERE players.user_id = ajar_users.user_id;

WITH duchess_users AS (
    WITH acolyte1 AS (
        SELECT players.user_id, acolyte_list.effect_num[1][acolytes.copies]
        FROM players
        INNER JOIN acolytes
            ON players.acolyte1 = acolytes.acolyte_id
        INNER JOIN acolyte_list
            ON acolytes.acolyte_name = acolyte_list.name
        WHERE acolytes.acolyte_name = 'Duchess'
    ),
    acolyte2 AS (
        SELECT players.user_id, acolyte_list.effect_num[1][acolytes.copies]
        FROM players
        INNER JOIN acolytes
            ON players.acolyte2 = acolytes.acolyte_id
        INNER JOIN acolyte_list
            ON acolytes.acolyte_name = acolyte_list.name
        WHERE acolytes.acolyte_name = 'Duchess'
    )
    SELECT * FROM acolyte1
    UNION
    SELECT * FROM acolyte2
)
UPDATE players
SET gravitas = gravitas + duchess_users.effect_num
FROM duchess_users
WHERE players.user_id = duchess_users.user_id;