<?php
require_once 'connection.php';
session_start();
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$user_id = $_SESSION['user_id'] ?? $_GET['user_id'] ?? null;
if (!$user_id) {
    echo json_encode(['success' => false, 'message' => 'User not logged in']);
    exit;
}

$stmt = $conn->prepare('SELECT id, quiz_content, question_count, created_at FROM quizzes WHERE user_id = ? ORDER BY created_at DESC');
$stmt->bind_param('s', $user_id);
$stmt->execute();
$result = $stmt->get_result();
$history = [];
while ($row = $result->fetch_assoc()) {
    $history[] = $row;
}
$stmt->close();
$conn->close();
echo json_encode(['success' => true, 'history' => $history]); 

