-- Training only. LEFT JOIN exposes broken references rather than dropping pairs.
SELECT COUNT(*) AS pairs,
       SUM(CASE WHEN p.label=1 THEN 1 ELSE 0 END) AS labeled_matches,
       SUM(CASE WHEN l.listing_id IS NULL OR r.listing_id IS NULL THEN 1 ELSE 0 END) AS broken_references,
       SUM(CASE WHEN l.title IS NULL OR trim(l.title)='' OR
                          r.title IS NULL OR trim(r.title)='' THEN 1 ELSE 0 END) AS pairs_with_missing_title,
       SUM(CASE WHEN l.brand IS NULL OR trim(l.brand)='' OR
                          r.brand IS NULL OR trim(r.brand)='' THEN 1 ELSE 0 END) AS pairs_with_missing_brand
FROM labeled_pairs AS p
LEFT JOIN listings AS l ON l.listing_id=p.left_id
LEFT JOIN listings AS r ON r.listing_id=p.right_id
WHERE p.split_name='train';
