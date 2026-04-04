// tests/App.test.jsx
import { render, screen } from '@testing-library/react';
import App from '../src/App';

test('renders login page by default when not authenticated', () => {
  render(<App />);
  expect(screen.getByText(/welcome back/i)).toBeInTheDocument();
});
