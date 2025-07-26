<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

require_once 'connection.php';
session_start();

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['success' => false, 'message' => 'User not logged in']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);

if (!isset($data['monitor_id']) || !isset($data['title']) || !isset($data['quiz']) || !isset($data['time'])) {
    echo json_encode(['success' => false, 'message' => 'All fields are required']);
    exit;
}

$monitor_id = $data['monitor_id'];
$title = $data['title'];
$quiz = $data['quiz'];
$time = $data['time'];
$user_id = $_SESSION['user_id'];
$score = isset($data['score']) ? $data['score'] : 0;

if (empty($title) || $quiz < 0 || $time < 0) {
    echo json_encode(['success' => false, 'message' => 'Invalid input values']);
    exit;
}

try {
    $stmt = $conn->prepare("UPDATE monitor SET title = ?, quiz = ?, time = ?, score = ? WHERE monitor_id = ? AND user_id = ?");
    if (!$stmt) {
        throw new Exception("Prepare failed: " . $conn->error);
    }
    
    $stmt->bind_param("siiiii", $title, $quiz, $time, $score, $monitor_id, $user_id);
    
    if ($stmt->execute()) {
        if ($stmt->affected_rows > 0) {
            echo json_encode(['success' => true, 'message' => 'Record updated successfully']);
        } else {
            echo json_encode(['success' => false, 'message' => 'Record not found or not authorized']);
        }
    } else {
        throw new Exception("Execute failed: " . $stmt->error);
    }
} catch (Exception $e) {
    error_log("Update monitor error: " . $e->getMessage());
    echo json_encode(['success' => false, 'message' => 'Database error: ' . $e->getMessage()]);
} finally {
    if (isset($stmt)) {
        $stmt->close();
    }
    if (isset($conn)) {
        $conn->close();
    }
}
?> 
