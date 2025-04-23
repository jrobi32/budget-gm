// TeamBuilder component for the $5 budget system
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import './TeamBuilder.css';

const TeamBuilder = ({ onError, nickname }) => {
    const [playerPool, setPlayerPool] = useState({});
    const [selectedPlayers, setSelectedPlayers] = useState([]);
    const [playerOptions, setPlayerOptions] = useState([]);
    const [budget, setBudget] = useState(5);
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [simulationResults, setSimulationResults] = useState(null);
    const [isSimulated, setIsSimulated] = useState(false);

    // Filter players based on current state
    const filterPlayers = useCallback((pool, currentSelectedPlayers) => {
        const options = [];
        ['$5', '$4', '$3', '$2', '$1'].forEach(category => {
            if (pool[category]) {
                const players = pool[category].filter(player => 
                    !currentSelectedPlayers.some(p => p.name === player.name)
                );
                if (players.length > 0) {
                    options.push(...players.map(player => ({
                        ...player,
                        cost: parseInt(category.replace('$', ''))
                    })));
                }
            }
        });
        return options;
    }, []);

    // Update available player options
    const updatePlayerOptions = useCallback((pool) => {
        const filteredOptions = filterPlayers(pool, selectedPlayers);
        setPlayerOptions(filteredOptions);
    }, [filterPlayers, selectedPlayers]);

    // Load player pool from backend
    const loadPlayerPool = useCallback(async () => {
        setIsLoading(true);
        try {
            const response = await axios.get('/api/player-pool');
            const newPlayerPool = response.data;
            setPlayerPool(newPlayerPool);
            updatePlayerOptions(newPlayerPool);
            setError('');
        } catch (err) {
            setError('Error loading player pool: ' + (err.response?.data?.message || err.message));
            if (onError) onError(err);
        } finally {
            setIsLoading(false);
        }
    }, [updatePlayerOptions, onError]);

    // Initial load
    useEffect(() => {
        loadPlayerPool();
    }, [loadPlayerPool]);

    // Handle player selection
    const selectPlayer = useCallback((player) => {
        if (isSimulated) {
            setError('Cannot make changes after simulation');
            return;
        }
        
        if (selectedPlayers.length >= 5) {
            setError('You can only select 5 players!');
            return;
        }

        if (player.cost > budget) {
            setError(`Not enough budget! You need $${player.cost} but only have $${budget} remaining.`);
            return;
        }

        setSelectedPlayers(prev => [...prev, player]);
        setBudget(prev => prev - player.cost);
        updatePlayerOptions(playerPool);
        setError('');
    }, [budget, isSimulated, selectedPlayers.length, playerPool, updatePlayerOptions]);

    // Handle player removal
    const removePlayer = useCallback((playerName) => {
        if (isSimulated) {
            setError('Cannot remove players after simulation');
            return;
        }
        
        const player = selectedPlayers.find(p => p.name === playerName);
        if (player) {
            setSelectedPlayers(prev => prev.filter(p => p.name !== playerName));
            setBudget(prev => prev + player.cost);
            updatePlayerOptions(playerPool);
        }
    }, [isSimulated, playerPool, selectedPlayers, updatePlayerOptions]);

    // Simulate team performance
    const simulateTeam = useCallback(async () => {
        if (selectedPlayers.length !== 5) {
            setError('Team must have exactly 5 players');
            return;
        }

        if (!nickname || nickname.trim() === '') {
            setError('Please enter your nickname before simulating');
            return;
        }

        setIsLoading(true);
        try {
            const response = await axios.post('/api/simulate-team', {
                players: selectedPlayers.map(p => ({
                    name: p.name,
                    cost: p.cost,
                    stats: p.stats || {}
                })),
                player_name: nickname.trim()
            });
            
            const data = response.data;
            if (!data || !data.wins || !data.losses) {
                throw new Error('Invalid response from server');
            }
            
            setSimulationResults(data);
            setIsSimulated(true);
            setError('');
        } catch (err) {
            console.error('Error simulating team:', err);
            setError(`Error simulating team: ${err.message}`);
            if (onError) onError(err);
        } finally {
            setIsLoading(false);
        }
    }, [selectedPlayers, nickname, onError]);

    if (isLoading) {
        return <div className="loading">Loading...</div>;
    }

    return (
        <div className="team-builder">
            <div className="team-section">
                <h2>Your Team</h2>
                <div className="budget-display">
                    Remaining Budget: ${budget}
                </div>
                <div className="selected-players">
                    {selectedPlayers.map((player, index) => (
                        <div key={index} className="player-card">
                            <div className="player-image">
                                <img 
                                    src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.id}.png`} 
                                    alt={player.name}
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&background=1E88E5&color=fff&size=200&bold=true&format=svg`;
                                    }}
                                />
                            </div>
                            <div className="player-info">
                                <h3>{player.name}</h3>
                                <p>Cost: ${player.cost}</p>
                                {player.stats && (
                                    <div className="player-stats">
                                        <p>PTS: {player.stats.pts?.toFixed(1) || '0.0'}</p>
                                        <p>AST: {player.stats.ast?.toFixed(1) || '0.0'}</p>
                                        <p>REB: {player.stats.reb?.toFixed(1) || '0.0'}</p>
                                        <p>STL: {player.stats.stl?.toFixed(1) || '0.0'}</p>
                                        <p>BLK: {player.stats.blk?.toFixed(1) || '0.0'}</p>
                                        <p>FG%: {(player.stats.fg_pct * 100)?.toFixed(1) || '0.0'}%</p>
                                        <p>3P%: {(player.stats.three_pct * 100)?.toFixed(1) || '0.0'}%</p>
                                    </div>
                                )}
                            </div>
                            <button 
                                className="remove-button"
                                onClick={() => removePlayer(player.name)}
                                disabled={isSimulated}
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                </div>
                {selectedPlayers.length === 5 && !isSimulated && (
                    <button 
                        className="simulate-button"
                        onClick={simulateTeam}
                        disabled={!nickname || nickname.trim() === ''}
                    >
                        Simulate Season
                    </button>
                )}
                {simulationResults && (
                    <div className="record-display">
                        <h3>Season Results</h3>
                        <p>Record: {simulationResults.wins}-{simulationResults.losses}</p>
                        <p>Win Probability: {(simulationResults.win_probability * 100).toFixed(1)}%</p>
                        {simulationResults.team_stats && (
                            <div className="team-stats">
                                <h4>Team Statistics</h4>
                                <p>Points per Game: {simulationResults.team_stats.PTS.toFixed(1)}</p>
                                <p>Assists per Game: {simulationResults.team_stats.AST.toFixed(1)}</p>
                                <p>Rebounds per Game: {simulationResults.team_stats.REB.toFixed(1)}</p>
                                <p>Steals per Game: {simulationResults.team_stats.STL.toFixed(1)}</p>
                                <p>Blocks per Game: {simulationResults.team_stats.BLK.toFixed(1)}</p>
                            </div>
                        )}
                    </div>
                )}
            </div>
            <div className="player-section">
                <h2>Available Players</h2>
                <div className="player-options">
                    {playerOptions.map((player, index) => (
                        <div key={index} className="player-card">
                            <div className="player-image">
                                <img 
                                    src={`https://cdn.nba.com/headshots/nba/latest/1040x760/${player.id}.png`} 
                                    alt={player.name}
                                    onError={(e) => {
                                        e.target.onerror = null;
                                        e.target.src = `https://ui-avatars.com/api/?name=${encodeURIComponent(player.name)}&background=1E88E5&color=fff&size=200&bold=true&format=svg`;
                                    }}
                                />
                            </div>
                            <div className="player-info">
                                <h3>{player.name}</h3>
                                <p>Cost: ${player.cost}</p>
                                {player.stats && (
                                    <div className="player-stats">
                                        <p>PTS: {player.stats.pts?.toFixed(1) || '0.0'}</p>
                                        <p>AST: {player.stats.ast?.toFixed(1) || '0.0'}</p>
                                        <p>REB: {player.stats.reb?.toFixed(1) || '0.0'}</p>
                                        <p>STL: {player.stats.stl?.toFixed(1) || '0.0'}</p>
                                        <p>BLK: {player.stats.blk?.toFixed(1) || '0.0'}</p>
                                        <p>FG%: {(player.stats.fg_pct * 100)?.toFixed(1) || '0.0'}%</p>
                                        <p>3P%: {(player.stats.three_pct * 100)?.toFixed(1) || '0.0'}%</p>
                                    </div>
                                )}
                            </div>
                            <button 
                                className="select-button"
                                onClick={() => selectPlayer(player)}
                                disabled={budget < player.cost || selectedPlayers.length >= 5 || isSimulated}
                            >
                                Select
                            </button>
                        </div>
                    ))}
                </div>
            </div>
            {error && <div className="error-message">{error}</div>}
        </div>
    );
};

export default TeamBuilder; 