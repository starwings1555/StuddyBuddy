<?php
require_once 'connection.php';
session_start();

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $user_name = $_POST['user_name'] ?? '';
    $password = $_POST['password'] ?? '';
    $email = $_POST['email'] ?? '';

    if (!empty($user_name) && !empty($password) && !empty($email)) {
        if (stripos($email, 'uitm') === false) {
            $error = "sorry, you're not within the organizations";
        } else {
            $stmt = $conn->prepare("SELECT user_id FROM users WHERE user_name = ? OR email = ? LIMIT 1");
            $stmt->bind_param("ss", $user_name, $email);
            $stmt->execute();
            $stmt->store_result();
            if ($stmt->num_rows > 0) {
                $error = "Username or email already registered.";
                $stmt->close();
            } else {
                $stmt->close();
                $user_id = rand(1000000000000000, 9999999999999999);
                $stmt = $conn->prepare("INSERT INTO users (user_id, user_name, email, password) VALUES (?, ?, ?, ?)");
                $stmt->bind_param("isss", $user_id, $user_name, $email, $password);
                if ($stmt->execute()) {
                    $_SESSION['user_id'] = $user_id;
                    header("Location: index.html?user_id=" . $user_id);
                    exit;
                } else {
                    $error = "Signup failed: " . $conn->error;
                }
                $stmt->close();
            }
        }
    } else {
        $error = "Please enter username, email, and password.";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Signup</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container py-5">
    <h2 class="mb-4">Signup</h2>
    <?php if (isset($error)): ?>
        <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
    <?php endif; ?>
    <form method="post">
        <div class="mb-3">
            <label for="user_name" class="form-label">Username</label>
            <input type="text" class="form-control" id="user_name" name="user_name" required>
        </div>
        <div class="mb-3">
            <label for="email" class="form-label">Email</label>
            <input type="email" class="form-control" id="email" name="email" required>
        </div>
        <div class="mb-3">
            <label for="password" class="form-label">Password</label>
            <input type="password" class="form-control" id="password" name="password" required>
        </div>
        <div class="d-flex gap-2">
            <button type="submit" class="btn btn-primary">Signup</button>
            <a href="login.php" class="btn btn-secondary">Back</a>
        </div>
    </form>
</body>
</html>
            
