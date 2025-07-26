<?php
header('Content-Type: application/json');
require_once 'connection.php';

$data = json_decode(file_get_contents('php://input'), true);
$userId = $data['user_id'] ?? null;
$newUsername = $data['new_username'] ?? null;

error_log("Received data: " . print_r($data, true));
error_log("User ID: " . $userId);
error_log("New Username: " . $newUsername);

if (!$userId || !$newUsername) {
    echo json_encode(['success' => false, 'message' => 'Missing required fields']);
    exit;
}

try {
    $checkStmt = $conn->prepare("SELECT user_id FROM users WHERE user_id = ?");
    $checkStmt->bind_param("s", $userId);
    $checkStmt->execute();
    $result = $checkStmt->get_result();
    
    if ($result->num_rows === 0) {
        error_log("User not found with ID: " . $userId);
        echo json_encode(['success' => false, 'message' => 'User not found']);
        exit;
    }
    
    $stmt = $conn->prepare("UPDATE users SET user_name = ? WHERE user_id = ?");
    $stmt->bind_param("ss", $newUsername, $userId);
    
    if ($stmt->execute()) {
        error_log("Username updated successfully for user ID: " . $userId);
        echo json_encode(['success' => true]);
    } else {
        error_log("Failed to update username. MySQL Error: " . $stmt->error);
        echo json_encode(['success' => false, 'message' => 'Failed to update username: ' . $stmt->error]);
    }
} catch (Exception $e) {
    error_log("Exception occurred: " . $e->getMessage());
    echo json_encode(['success' => false, 'message' => 'Database error: ' . $e->getMessage()]);
}
?> 

