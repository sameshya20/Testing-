import React, { useState } from 'react';
import type { TestCase } from '../types';
import { X, Save } from 'lucide-react';

interface EditTestCaseModalProps {
  testCase: TestCase;
  onSave: (updated: TestCase) => void;
  onClose: () => void;
}

export const EditTestCaseModal: React.FC<EditTestCaseModalProps> = ({ testCase, onSave, onClose }) => {
  const [scenario, setScenario] = useState(testCase.scenario);
  const [description, setDescription] = useState(testCase.description);
  const [preconditions, setPreconditions] = useState(testCase.preconditions);
  const [testData, setTestData] = useState(testCase.test_data);
  const [priority, setPriority] = useState(testCase.priority);
  const [expectedResult, setExpectedResult] = useState(testCase.expected_result);
  const [stepsText, setStepsText] = useState(testCase.test_steps.join('\n'));

  const handleSave = () => {
    const updatedSteps = stepsText.split('\n').filter((s) => s.trim().length > 0);
    onSave({
      ...testCase,
      scenario,
      description,
      preconditions,
      test_data: testData,
      priority,
      expected_result: expectedResult,
      test_steps: updatedSteps
    });
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-slate-900 border border-slate-800 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-xl">
        
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 border-b border-slate-800 bg-slate-950">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-semibold text-white">Edit Test Case:</span>
            <span className="font-mono text-xs font-bold text-blue-400">{testCase.id}</span>
            <span className="text-slate-600">·</span>
            <span className="text-xs text-slate-400 font-mono">{testCase.requirement_ref}</span>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-slate-400 hover:text-white p-1 rounded hover:bg-slate-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="p-5 space-y-3.5 text-xs">
          <div>
            <label className="block text-slate-300 font-medium mb-1">Priority</label>
            <select
              value={priority}
              onChange={(e) => setPriority(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
            >
              <option value="High">High Priority</option>
              <option value="Medium">Medium Priority</option>
              <option value="Low">Low Priority</option>
            </select>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Test Scenario</label>
            <input
              type="text"
              value={scenario}
              onChange={(e) => setScenario(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Test Description</label>
            <textarea
              rows={2}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-slate-300 font-medium mb-1">Preconditions</label>
              <input
                type="text"
                value={preconditions}
                onChange={(e) => setPreconditions(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
              />
            </div>

            <div>
              <label className="block text-slate-300 font-medium mb-1">Test Data</label>
              <input
                type="text"
                value={testData}
                onChange={(e) => setTestData(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500 font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Test Steps (One per line)</label>
            <textarea
              rows={4}
              value={stepsText}
              onChange={(e) => setStepsText(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 font-mono focus:outline-none focus:border-blue-500 leading-relaxed"
            />
          </div>

          <div>
            <label className="block text-slate-300 font-medium mb-1">Expected Result</label>
            <textarea
              rows={2}
              value={expectedResult}
              onChange={(e) => setExpectedResult(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded px-2.5 py-1.5 text-xs text-slate-100 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end space-x-2 px-5 py-3 bg-slate-950 border-t border-slate-800">
          <button
            type="button"
            onClick={onClose}
            className="px-3 py-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-750 border border-slate-700 rounded transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            className="px-3 py-1.5 text-xs text-white bg-blue-600 hover:bg-blue-500 rounded font-medium flex items-center space-x-1.5 transition-colors cursor-pointer"
          >
            <Save className="w-3.5 h-3.5" />
            <span>Save Changes</span>
          </button>
        </div>

      </div>
    </div>
  );
};
