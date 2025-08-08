import ReactDOM from 'react-dom/client';
import App from './App';
import './i18n/config';
import './index.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement,
);
root.render(<App />);
