'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/utils/api';

export default function SignupForm() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!formData.email || !formData.password || !formData.confirmPassword || !formData.fullName) {
      setError('All fields are required');
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    try {
      setLoading(true);
      const response = await authAPI.signup({
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName,
      });

      localStorage.setItem('token', (response as any).access_token);
      localStorage.setItem(
        'user',
        JSON.stringify(
          (response as any).user || {
            email: formData.email,
            name: formData.fullName,
          }
        )
      );

      router.push('/design');
    } catch (err: any) {
      setError(err.message || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      {error && (
        <div className="auth-alert" role="alert">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="auth-field-group">
          <label htmlFor="signup-full-name" className="auth-label">
            Full Name
          </label>
          <input
            id="signup-full-name"
            type="text"
            name="fullName"
            value={formData.fullName}
            onChange={handleChange}
            placeholder="Shashi Rao"
            className="auth-input"
          />
        </div>

        <div className="auth-field-group">
          <label htmlFor="signup-email" className="auth-label">
            Email
          </label>
          <input
            id="signup-email"
            type="email"
            name="email"
            value={formData.email}
            onChange={handleChange}
            placeholder="you@siliquesta.io"
            className="auth-input"
          />
        </div>

        <div className="auth-field-group">
          <label htmlFor="signup-password" className="auth-label">
            Password
          </label>
          <input
            id="signup-password"
            type="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            placeholder="Minimum 8 characters"
            className="auth-input"
          />
        </div>

        <div className="auth-field-group">
          <label htmlFor="signup-confirm-password" className="auth-label">
            Confirm Password
          </label>
          <input
            id="signup-confirm-password"
            type="password"
            name="confirmPassword"
            value={formData.confirmPassword}
            onChange={handleChange}
            placeholder="Repeat your password"
            className="auth-input"
          />
        </div>

        <button type="submit" disabled={loading} className="auth-submit">
          {loading ? 'Creating account...' : 'Create Account'}
        </button>
      </form>

      <div className="auth-assist">
        <span>Already provisioned? Jump back into your workspace.</span>
        <Link href="/auth/login">Go to login</Link>
      </div>
    </>
  );
}
