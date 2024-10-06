SELECT student_id, COUNT(*) AS graded_assignment_count
FROM assignments
WHERE state IN ('GRADED', 'SUBMITTED')  -- Adjust based on your grading states
GROUP BY student_id
ORDER BY graded_assignment_count DESC;  -- Optional: to order by the count
