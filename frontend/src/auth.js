// src/Login.js
import React, { useState } from "react";
import { loginUser } from "./api";

function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async () => {
    const res = await loginUser(email, password);
    if (res.access_token) {
      alert("✅ Login successful");
      localStorage.setItem("token", res.access_token);
    } else {
      alert("❌ Login failed");
    }
  };

  return (
    <div>
      <h2>Login</h2>
      <input placeholder="Email" onChange={(e) => setEmail(e.target.value)} />
      <br />
      <input
        type="password"
        placeholder="Password"
        onChange={(e) => setPassword(e.target.value)}
      />
      <br />
      <button onClick={handleSubmit}>Login</button>
      <p>Don't have an account? <a href="/register">Register here</a></p>
    </div>
  );
}

export default Login;
