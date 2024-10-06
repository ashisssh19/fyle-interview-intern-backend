WITH graded_assignments AS (
    SELECT teacher_id, COUNT(*) AS total_assignments
    FROM assignments
    WHERE state = 'GRADED'
    GROUP BY teacher_id
),
grade_a_assignments AS (
    SELECT teacher_id, COUNT(*) AS grade_A_count
    FROM assignments
    WHERE grade = 'A' AND state = 'GRADED'
    GROUP BY teacher_id
)
SELECT g.teacher_id, COALESCE(a.grade_A_count, 0) AS grade_A_count
FROM graded_assignments g
LEFT JOIN grade_a_assignments a ON g.teacher_id = a.teacher_id
ORDER BY g.total_assignments DESC
LIMIT 1;