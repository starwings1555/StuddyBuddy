<?php
header('Content-Type: application/json');
require_once 'connection.php';

$data = json_decode(file_get_contents('php://input'), true);
$userId = $data['user_id'] ?? null;
$newPassword = $data['new_password'] ?? null;

error_log("Received data: " . print_r($data, true));
error_log("User ID: " . $userId);
error_log("New Password: " . $newPassword);

if (!$userId || !$newPassword) {
    echo json_encode(['success' => false, 'message' => 'Missing required fields']);
    exit;
}

try {
    $plainPassword = $newPassword;
    error_log("Plain Password: " . $plainPassword);
    
    $checkStmt = $conn->prepare("SELECT user_id FROM users WHERE user_id = ?");
    $checkStmt->bind_param("s", $userId);
    $checkStmt->execute();
    $result = $checkStmt->get_result();
    
    if ($result->num_rows === 0) {
        error_log("User not found with ID: " . $userId);
        echo json_encode(['success' => false, 'message' => 'User not found']);
        exit;
    }
    
    $stmt = $conn->prepare("UPDATE users SET password = ? WHERE user_id = ?");
    $stmt->bind_param("ss", $plainPassword, $userId);
    
    if ($stmt->execute()) {
        error_log("Password updated successfully for user ID: " . $userId);
        echo json_encode(['success' => true]);
    } else {
        error_log("Failed to update password. MySQL Error: " . $stmt->error);
        echo json_encode(['success' => false, 'message' => 'Failed to update password: ' . $stmt->error]);
    }
} catch (Exception $e) {
    error_log("Exception occurred: " . $e->getMessage());
    echo json_encode(['success' => false, 'message' => 'Database error: ' . $e->getMessage()]);
}
?> 
