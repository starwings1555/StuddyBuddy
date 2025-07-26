<?php
header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST');
header('Access-Control-Allow-Headers: Content-Type');

error_reporting(E_ALL);
ini_set('display_errors', 1);

require_once 'connection.php';

session_start();

if (!isset($_SESSION['user_id'])) {
    echo json_encode(['success' => false, 'message' => 'User not logged in']);
    exit;
}

if (!isset($conn) || $conn->connect_error) {
    echo json_encode(['success' => false, 'message' => 'Database connection failed']);
    exit;
}

$data = json_decode(file_get_contents('php://input'), true);

if (!$data) {
    echo json_encode(['success' => false, 'message' => 'Invalid data format']);
    exit;
}

$user_id = $_SESSION['user_id'];
$title = $data['title'] ?? '';
$quiz = $data['corrected'] ?? 0;
$time = $data['timeTaken'] ?? 0;
$score = $data['score'] ?? 0;

if (empty($title) || $quiz < 0 || $time < 0) {
    echo json_encode(['success' => false, 'message' => 'Invalid input values']);
    exit;
}

try {
    $stmt = $conn->prepare("INSERT INTO monitor (user_id, title, quiz, time, score) VALUES (?, ?, ?, ?, ?)");
    if (!$stmt) {
        throw new Exception("Prepare failed: " . $conn->error);
    }
    
    $stmt->bind_param("isiii", $user_id, $title, $quiz, $time, $score);
    
    if ($stmt->execute()) {
        echo json_encode(['success' => true, 'message' => 'Monitor data saved successfully']);
    } else {
        throw new Exception("Execute failed: " . $stmt->error);
    }
} catch (Exception $e) {
    error_log("Monitor submit error: " . $e->getMessage());
    echo json_encode(['success' => false, 'message' => 'Database error: ' . $e->getMessage()]);
} finally {
    if (isset($stmt)) {
        $stmt->close();
    }
    if (isset($conn)) {
        $conn->close();
    }
}
