import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App_应用';
import { loadLanguage, readLanguage } from './i18n_多语言';
import './styles_样式.css';

async function start(){
  let lang=readLanguage();
  try{await loadLanguage(lang);}catch{lang='ko';}
  ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><App initialLanguage={lang}/></React.StrictMode>);
}
void start();
