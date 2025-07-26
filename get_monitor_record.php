<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET');
header('Access-Control-Allow-Headers: Content-Type');

require_once 'connection.php';
session_start();

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['success' => false, 'message' => 'User not logged in']);
    exit;
}

$user_id = $_SESSION['user_id'];

try {
    $stmt = $conn->prepare("SELECT monitor_id, title, quiz, time, score, Date FROM monitor WHERE user_id = ? ORDER BY monitor_id DESC");
    $stmt->bind_param("i", $user_id);
    $stmt->execute();
    $result = $stmt->get_result();
    
    $records = [];
    while ($row = $result->fetch_assoc()) {
        $records[] = [
            'id' => $row['monitor_id'],
            'title' => $row['title'],
            'corrected_quiz_count' => $row['quiz'],
            'time_taken' => $row['time'],
            'score' => $row['score'],
            'date' => $row['Date']
        ];
    }
    
    echo json_encode(['success' => true, 'records' => $records]);
} catch (Exception $e) {
    error_log("Get monitor records error: " . $e->getMessage());
    echo json_encode(['success' => false, 'message' => 'Database error: ' . $e->getMessage()]);
}

$stmt->close();
$conn->close();
?> 
