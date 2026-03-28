// tests/App.test.jsx
import { render, screen } from '@testing-library/react';
import App from '../src/App';

test('renders header', () => {
  render(<App />);
  expect(screen.getByText(/intelligent job matching/i)).toBeInTheDocument();
});