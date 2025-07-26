<?php
require_once 'connection.php';
session_start();
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    echo json_encode(['success' => false, 'message' => 'Invalid request method']);
    exit;
}

$user_id = $_SESSION['user_id'] ?? null;
if (!$user_id) {
    echo json_encode(['success' => false, 'message' => 'User not logged in']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);
$quiz_id = $data['id'] ?? null;
if (!$quiz_id) {
    echo json_encode(['success' => false, 'message' => 'Quiz ID required']);
    exit;
}

$stmt = $conn->prepare('DELETE FROM quizzes WHERE id = ? AND user_id = ?');
$stmt->bind_param('is', $quiz_id, $user_id);
if ($stmt->execute()) {
    if ($stmt->affected_rows > 0) {
        echo json_encode(['success' => true]);
    } else {
        echo json_encode(['success' => false, 'message' => 'Quiz not found or not authorized']);
    }
} else {
    echo json_encode(['success' => false, 'message' => 'Database error']);
}
$stmt->close();
$conn->close(); 

