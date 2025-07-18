<?php
require_once 'connection.php';
session_start();

if ($_SERVER['REQUEST_METHOD'] == 'POST') {
    $user_name = $_POST['user_name'] ?? '';
    $password = $_POST['password'] ?? '';

    if (!empty($user_name) && !empty($password)) {
        $stmt = $conn->prepare("SELECT * FROM users WHERE user_name = ? LIMIT 1");
        $stmt->bind_param("s", $user_name);
        $stmt->execute();
        $result = $stmt->get_result();

        if ($result && $result->num_rows > 0) {
            $user_data = $result->fetch_assoc();
            if ($password === $user_data['password']) {
                $_SESSION['user_id'] = $user_data['user_id'];
                header("Location: index.html?user_id=" . $user_data['user_id']);
                exit;
            } else {
                $error = "Wrong username or password!";
            }
        } else {
            $error = "Wrong username or password!";
        }
        $stmt->close();
    } else {
        $error = "Please enter both username and password.";
    }
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Login</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="container py-5">
  <h2 class="mb-4">Login</h2>
  <?php if (isset($error)): ?>
    <div class="alert alert-danger"><?php echo htmlspecialchars($error); ?></div>
  <?php endif; ?>
  <form method="post">
    <div class="mb-3">
      <label for="user_name" class="form-label">Username</label>
      <input type="text" class="form-control" id="user_name" name="user_name" required>
    </div>
    <div class="mb-3">
      <label for="password" class="form-label">Password</label>
      <input type="password" class="form-control" id="password" name="password" required>
    </div>
    <div class="d-flex gap-2">
      <button type="submit" class="btn btn-primary">Login</button>
      <a href="signup.php" class="btn btn-secondary">Signup</a>
    </div>
  </form>
</body>
</html>
