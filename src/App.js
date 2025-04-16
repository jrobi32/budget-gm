import React from 'react';
import './App.css';
import TeamBuilder from './components/TeamBuilder';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>NBA Team Builder</h1>
      </header>
      <main>
        <TeamBuilder />
      </main>
    </div>
  );
}

export default App;
