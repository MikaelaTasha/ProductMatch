-- Counts by original split. These are dataset counts, not model performance.
SELECT split_name, COUNT(*) AS pairs, SUM(label) AS matches
FROM labeled_pairs GROUP BY split_name;

-- Training examples only: join each pair to its two original listings.
SELECT p.pair_id, l.title AS left_title, r.title AS right_title, p.label
FROM labeled_pairs AS p
JOIN listings AS l ON l.listing_id = p.left_id
JOIN listings AS r ON r.listing_id = p.right_id
WHERE p.split_name = 'train'
ORDER BY p.pair_id
LIMIT 5;

-- Inspect known overlap without displaying test listing content.
WITH split_offers AS (
    SELECT split_name, left_id AS listing_id FROM labeled_pairs
    UNION
    SELECT split_name, right_id AS listing_id FROM labeled_pairs
)
SELECT a.split_name AS first_split, b.split_name AS second_split,
       COUNT(*) AS shared_offer_ids
FROM split_offers AS a
JOIN split_offers AS b ON a.listing_id = b.listing_id
WHERE a.split_name < b.split_name
GROUP BY a.split_name, b.split_name;
