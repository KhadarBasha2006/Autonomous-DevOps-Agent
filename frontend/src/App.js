import React, { useState } from 'react';
import axios from 'axios';
import { Play, CheckCircle, XCircle, Clock, GitBranch, AlertTriangle, Terminal, RefreshCw, Link as LinkIcon } from 'lucide-react';

const App = () => {
  const [formData, setFormData] = useState({
    repoUrl: '',
    teamName: '',
    leaderName: '',
    githubToken: ''
  });
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const handleRun = async () => {
    if (!formData.repoUrl || !formData.teamName || !formData.leaderName) {
      setError('Please fill in all required fields');
      return;
    }
    
    setError('');
    setLoading(true);
    setResults(null);
    
    try {
      const response = await axios.post('http://localhost:8000/analyze', {
        repo_url: formData.repoUrl,
        team_name: formData.teamName,
        leader_name: formData.leaderName,
        github_token: formData.githubToken
      });
      setResults(response.data);
    } catch (err) {
      console.error("Agent failed", err);
      setError(err.response?.data?.detail || "Agent execution failed. Check console.");
    }
    setLoading(false);
  };

  const calculateScore = () => {
    if (!results) return 0;
    let score = 100;
    if (results.total_time_taken < 300) score += 10;
    if (results.total_fixes_applied > 20) {
      score -= (results.total_fixes_applied - 20) * 2;
    }
    return Math.max(score, 0);
  };

  const getBugTypeColor = (bugType) => {
    switch(bugType) {
      case 'LINTING': return 'bg-yellow-900 text-yellow-200';
      case 'SYNTAX': return 'bg-red-900 text-red-200';
      case 'TYPE_ERROR': return 'bg-purple-900 text-purple-200';
      case 'INDENTATION': return 'bg-blue-900 text-blue-200';
      case 'IMPORT': return 'bg-orange-900 text-orange-200';
      default: return 'bg-gray-700 text-gray-200';
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white p-4 md:p-8 font-sans">
      <div className="max-w-6xl mx-auto">
        
        {/* HEADER */}
        <header className="mb-8 flex flex-col md:flex-row justify-between items-start md:items-center border-b border-slate-700 pb-4">
          <div>
            <h1 className="text-3xl font-bold text-blue-400">Autonomous DevOps Agent</h1>
            <p className="text-slate-400 text-sm mt-1">RIFT Challenge 2026</p>
          </div>
          <div className="mt-4 md:mt-0">
            <span className="px-3 py-1 bg-blue-600 rounded-full text-sm font-semibold">AI-Powered Healing</span>
          </div>
        </header>

        {/* ERROR MESSAGE */}
        {error && (
          <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded-lg mb-6 flex items-center gap-2">
            <XCircle size={20} />
            {error}
          </div>
        )}

        {/* INPUT SECTION */}
        <div className="bg-slate-800 p-6 rounded-lg shadow-lg mb-8">
          <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
            <Terminal size={20} className="text-blue-400" />
            Repository Configuration
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-sm text-slate-400 mb-1">GitHub Repository URL *</label>
              <input 
                type="text" 
                placeholder="https://github.com/username/repo" 
                className="w-full p-3 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:border-blue-500 text-white"
                value={formData.repoUrl}
                onChange={(e) => setFormData({...formData, repoUrl: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Team Name *</label>
              <input 
                type="text" 
                placeholder="RIFT ORGANISERS" 
                className="w-full p-3 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:border-blue-500 text-white"
                value={formData.teamName}
                onChange={(e) => setFormData({...formData, teamName: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Team Leader Name *</label>
              <input 
                type="text" 
                placeholder="Saiyam Kumar" 
                className="w-full p-3 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:border-blue-500 text-white"
                value={formData.leaderName}
                onChange={(e) => setFormData({...formData, leaderName: e.target.value})}
              />
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">GitHub Token (Optional)</label>
              <input 
                type="password" 
                placeholder="ghp_xxxxxxxxxxxx" 
                className="w-full p-3 bg-slate-700 rounded border border-slate-600 focus:outline-none focus:border-blue-500 text-white"
                value={formData.githubToken}
                onChange={(e) => setFormData({...formData, githubToken: e.target.value})}
              />
              <p className="text-xs text-slate-500 mt-1">If provided: forks to your account. If not: commits directly to original repo</p>
            </div>
          </div>
          <button 
            onClick={handleRun}
            disabled={loading}
            className={`flex items-center gap-2 px-8 py-3 rounded font-bold transition ${loading ? 'bg-slate-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500'}`}
          >
            {loading ? <><RefreshCw className="animate-spin"/> Running Agent...</> : <><Play size={20}/> Run Agent</>}
          </button>
        </div>

        {/* RESULTS SECTION */}
        {results && (
          <div className="space-y-6">
            
            {/* RUN SUMMARY CARD */}
            <div className="bg-slate-800 p-6 rounded-lg shadow-lg border-l-4 border-blue-500">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <CheckCircle className="text-blue-400"/> Run Summary
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
                <div className="bg-slate-700/50 p-3 rounded">
                  <div className="text-slate-400 mb-1">Repository</div>
                  <div className="truncate font-mono text-blue-300 text-xs">{results.repo_url}</div>
                </div>
                <div className="bg-slate-700/50 p-3 rounded">
                  <div className="text-slate-400 mb-1">Team / Leader</div>
                  <div>{results.team_name} / {results.leader_name}</div>
                </div>
                <div className="bg-slate-700/50 p-3 rounded">
                  <div className="text-slate-400 mb-1">Branch Created</div>
                  <div className="text-green-400 font-mono text-xs">{results.branch_name}</div>
                </div>
                <div className="bg-slate-700/50 p-3 rounded">
                  <div className="text-slate-400 mb-1">Time Taken</div>
                  <div className="flex items-center gap-1">
                    <Clock size={14}/> {results.total_time_taken}s
                  </div>
                </div>
              </div>
              
              {/* BRANCH URL DISPLAY */}
              <div className="mt-4 space-y-3">
                {/* GitHub Token Info */}
                <div className="p-3 bg-slate-700/50 rounded flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-sm text-slate-300">Token Used:</span>
                    <span className={`text-xs font-semibold px-2 py-1 rounded ${results.token_used.includes('User') ? 'bg-blue-600 text-blue-200' : 'bg-amber-600 text-amber-200'}`}>
                      {results.token_used}
                    </span>
                  </div>
                  <div className="text-sm text-slate-400">
                    Pushed to: <span className="font-semibold text-slate-200">{results.push_destination}</span>
                  </div>
                </div>

                {/* Branch URL */}
                <div className="p-3 bg-slate-700/50 rounded flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <GitBranch className="text-green-400" size={20}/>
                    <span className="text-sm text-slate-300">Fixed Branch URL:</span>
                  </div>
                  <a 
                    href={results.branch_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 text-sm font-mono flex items-center gap-1"
                  >
                    {results.branch_url}
                    <LinkIcon size={14}/>
                  </a>
                </div>
              </div>
              
              <div className="mt-4 flex flex-col md:flex-row items-start md:items-center gap-4">
                <div className="text-2xl font-bold">CI/CD Status: 
                  <span className={`ml-2 px-3 py-1 rounded text-sm ${results.cicd_status === 'PASSED' ? 'bg-green-600' : 'bg-red-600'}`}>
                    {results.cicd_status}
                  </span>
                </div>
                <div className="text-slate-400">
                  Iterations: {results.total_iterations}
                </div>
              </div>
            </div>

            {/* SCORE BREAKDOWN */}
            <div className="bg-slate-800 p-6 rounded-lg shadow-lg">
              <h2 className="text-xl font-bold mb-4">Score Breakdown</h2>
              <div className="flex items-end gap-4 h-40 mb-4">
                <div className="w-1/3 bg-blue-600 rounded-t flex flex-col justify-center items-center" style={{height: '100%'}}>
                  <div className="text-center mt-2 font-bold text-3xl">{calculateScore()}</div>
                  <div className="text-center text-xs">Total</div>
                </div>
                <div className="w-1/3 bg-slate-700 rounded-t flex flex-col justify-end items-center pb-2 h-4/5">
                  <div className="font-bold">100</div>
                  <div className="text-xs text-slate-400">Base</div>
                </div>
                <div className={`w-1/3 rounded-t flex flex-col justify-end items-center pb-2 h-3/5 ${results.total_time_taken < 300 ? 'bg-green-600' : 'bg-slate-700'}`}>
                  <div className="font-bold">+10</div>
                  <div className="text-xs text-slate-400">Speed</div>
                </div>
              </div>
              <div className="text-green-400 font-mono text-lg">
                Final Score: {calculateScore()} Points
              </div>
            </div>

            {/* FIXES TABLE */}
            <div className="bg-slate-800 p-6 rounded-lg shadow-lg overflow-x-auto">
              <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                <AlertTriangle size={20} className="text-yellow-400"/> 
                Fixes Applied ({results.fixes.length})
              </h2>
              {results.fixes.length === 0 ? (
                <p className="text-slate-400">No fixes were required.</p>
              ) : (
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-700 text-slate-400">
                      <th className="p-2">File</th>
                      <th className="p-2">Bug Type</th>
                      <th className="p-2">Line</th>
                      <th className="p-2">Commit Message</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Details</th>
                    </tr>
                  </thead>
                  <tbody>
                    {results.fixes.map((fix, idx) => (
                      <tr key={idx} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                        <td className="p-2 font-mono text-blue-300">{fix.file}</td>
                        <td className="p-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${getBugTypeColor(fix.bug_type)}`}>
                            {fix.bug_type}
                          </span>
                        </td>
                        <td className="p-2">{fix.line_number}</td>
                        <td className="p-2 font-mono text-xs text-slate-400">{fix.commit_message}</td>
                        <td className="p-2">
                          {fix.status === 'Fixed' ? (
                            <span className="text-green-400 flex items-center gap-1">
                              <CheckCircle size={14}/> Fixed
                            </span>
                          ) : (
                            <span className="text-red-400 flex items-center gap-1">
                              <XCircle size={14}/> Failed
                            </span>
                          )}
                        </td>
                        <td className="p-2 text-slate-300">{fix.fix_detail}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>

            {/* CI/CD TIMELINE */}
            <div className="bg-slate-800 p-6 rounded-lg shadow-lg">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold flex items-center gap-2">
                  <RefreshCw className="text-blue-400" size={20}/>
                  CI/CD Pipeline Iterations
                </h2>
                <div className="text-lg font-bold text-blue-300 bg-slate-700 px-3 py-1 rounded">
                  {results.total_iterations}/{results.cicd_runs?.length || 5}
                </div>
              </div>

              {results.cicd_runs && results.cicd_runs.length > 0 ? (
                <div className="space-y-3">
                  {results.cicd_runs.map((run, idx) => (
                    <div key={idx} className="flex items-center gap-4 p-4 bg-slate-700/50 rounded-lg hover:bg-slate-700 transition">
                      {/* Iteration Number and Badge */}
                      <div className="flex items-center gap-3 min-w-[120px]">
                        <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg
                          ${run.status === 'PASSED' ? 'bg-green-600 text-green-100' : run.status === 'FAILED' ? 'bg-red-600 text-red-100' : 'bg-yellow-600 text-yellow-100'}`}>
                          {idx + 1}
                        </div>
                        <div className="flex flex-col">
                          <div className="text-sm font-semibold text-slate-200">Iteration {idx + 1}</div>
                          <div className={`text-xs font-bold px-2 py-0.5 rounded-full w-fit
                            ${run.status === 'PASSED' ? 'bg-green-900/50 text-green-300' : run.status === 'FAILED' ? 'bg-red-900/50 text-red-300' : 'bg-yellow-900/50 text-yellow-300'}`}>
                            {run.status === 'PASSED' ? '✓ PASSED' : run.status === 'FAILED' ? '✗ FAILED' : '⟳ RUNNING'}
                          </div>
                        </div>
                      </div>

                      {/* Timeline Connector */}
                      {idx < results.cicd_runs.length - 1 && (
                        <div className={`flex-1 h-1 rounded
                          ${run.status === 'PASSED' ? 'bg-green-600/50' : run.status === 'FAILED' ? 'bg-red-600/50' : 'bg-yellow-600/50'}`}/>
                      )}

                      {/* Timestamp */}
                      {run.timestamp && (
                        <div className="text-xs text-slate-400 min-w-[150px] text-right">
                          <Clock size={12} className="inline mr-1"/>
                          {new Date(run.timestamp).toLocaleTimeString()}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-400">No CI/CD runs available</p>
              )}

              {/* Summary */}
              <div className="mt-6 p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                <div className="grid grid-cols-3 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-green-400">
                      {results.cicd_runs?.filter(r => r.status === 'PASSED').length || 0}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Passed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-red-400">
                      {results.cicd_runs?.filter(r => r.status === 'FAILED').length || 0}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Failed</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-blue-400">
                      {results.total_iterations || results.cicd_runs?.length || 0}
                    </div>
                    <div className="text-xs text-slate-400 mt-1">Total</div>
                  </div>
                </div>
              </div>
            </div>

          </div>
        )}
      </div>
    </div>
  );
};

export default App;