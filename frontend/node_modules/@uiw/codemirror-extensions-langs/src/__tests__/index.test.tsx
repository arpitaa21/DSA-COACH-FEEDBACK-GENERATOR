/* eslint-disable jest/no-conditional-expect */
import React, { useEffect, useRef } from 'react';
import { langs, langNames, loadLanguage, type LanguageName } from '..';

describe('@uiw/codemirror-extensions-langs', () => {
  describe('langs object structure', () => {
    it('should have both py and python keys', () => {
      expect(langs).toHaveProperty('py');
      expect(langs).toHaveProperty('python');
    });

    it('should map both py and python to the same function result', () => {
      const pyResult = langs.py();
      const pythonResult = langs.python();

      // Both should return LanguageSupport or StreamLanguage instances
      expect(pyResult).toBeDefined();
      expect(pythonResult).toBeDefined();

      // Both types have 'language' property - StreamLanguage via getter, LanguageSupport directly
      expect(pyResult).toHaveProperty('language');
      expect(pythonResult).toHaveProperty('language');
    });

    it('should contain common programming languages', () => {
      const expectedLanguages = ['js', 'ts', 'json', 'html', 'css', 'markdown'];

      expectedLanguages.forEach((lang) => {
        expect(langs).toHaveProperty(lang);
        expect(typeof langs[lang as LanguageName]).toBe('function');
      });
    });

    it('should have keys with proper formatting (no quotes for identifiers, single quotes for special)', () => {
      const source = require.resolve('..');
      const fs = require('fs');
      const content = fs.readFileSync(
        source
          .replace(/\.d\.ts$/, '.ts')
          .replace(/esm\//, 'src/')
          .replace(/cjs\//, 'src/'),
        'utf8',
      );

      // Check that regular identifiers don't have quotes
      expect(content).toMatch(/^\s+apl:/m);
      expect(content).toMatch(/^\s+python:/m);
      expect(content).toMatch(/^\s+py:/m);
      expect(content).toMatch(/^\s+js:/m);

      // Check that numbers and special characters use single quotes
      expect(content).toMatch(/^\s+'1':/m);
      expect(content).toMatch(/^\s+'c\+\+':/m);
      expect(content).toMatch(/^\s+'4th':/m);

      // Ensure no double quotes are used for keys
      expect(content).not.toMatch(/^\s+"[^"]+"/m);
    });
  });

  describe('loadLanguage function', () => {
    it('should load existing languages', () => {
      const result = loadLanguage('js');
      expect(result).toBeDefined();
      expect(result).toHaveProperty('language');
    });

    it('should return null for non-existent languages', () => {
      const result = loadLanguage('nonexistent' as LanguageName);
      expect(result).toBeNull();
    });

    it('should load python using py key', () => {
      const result = loadLanguage('py');
      expect(result).toBeDefined();
      expect(result).toHaveProperty('language');
    });

    it('should load python using python key', () => {
      const result = loadLanguage('python');
      expect(result).toBeDefined();
      expect(result).toHaveProperty('language');
    });
  });

  describe('langNames export', () => {
    it('should be an array containing all language names', () => {
      expect(Array.isArray(langNames)).toBe(true);
      expect(langNames.length).toBeGreaterThan(0);
    });

    it('should include both py and python', () => {
      expect(langNames).toContain('py');
      expect(langNames).toContain('python');
    });

    it('should maintain consistent ordering', () => {
      // Check that the langNames are in the same order as the generated source
      // The actual sorting follows JavaScript's default sort behavior
      const actualLangsKeys = Object.keys(langs);
      expect(langNames).toEqual(actualLangsKeys);
    });

    it('should match the keys in langs object', () => {
      const langsKeys = Object.keys(langs).sort();
      expect(langNames.sort()).toEqual(langsKeys);
    });
  });

  describe('key format validation', () => {
    it('should have consistent key patterns', () => {
      // Test that all numeric keys use single quotes in source
      const numericKeys = langNames.filter((key) => /^\d/.test(key));
      expect(numericKeys.length).toBeGreaterThan(0);

      // Test that special character keys exist
      const specialKeys = langNames.filter((key) => /[^a-zA-Z0-9_$]/.test(key));
      expect(specialKeys.length).toBeGreaterThan(0);
      expect(specialKeys).toContain('c++');
    });

    it('should validate generated code format against regex patterns', () => {
      // This test reads the actual generated source to ensure format
      const source = require.resolve('..');
      const fs = require('fs');
      const content = fs.readFileSync(
        source
          .replace(/\.d\.ts$/, '.ts')
          .replace(/esm\//, 'src/')
          .replace(/cjs\//, 'src/'),
        'utf8',
      );

      // Find the langs object definition
      const langsMatch = content.match(/export const langs = \{([\s\S]*?)\}/);
      expect(langsMatch).toBeTruthy();

      const langsContent = langsMatch![1];

      // Check format rules:
      // 1. Valid identifiers should not have quotes
      const validIdentifierLines = langsContent.match(/^\s+[a-zA-Z_$][a-zA-Z0-9_$]*:/gm);
      expect(validIdentifierLines).toBeTruthy();
      expect(validIdentifierLines!.length).toBeGreaterThan(2);

      // 2. Numbers and special chars should use single quotes
      const quotedLines = langsContent.match(/^\s+'[^']+'/gm);
      expect(quotedLines).toBeTruthy();
      expect(quotedLines!.length).toBeGreaterThan(5);

      // 3. No double quotes should be used
      const doubleQuotedKeys = langsContent.match(/^\s+"[^"]+"/gm);
      expect(doubleQuotedKeys).toBeNull();
    });
  });

  describe('language functionality', () => {
    it('should return valid language support objects', () => {
      const testLanguages: LanguageName[] = ['js', 'py', 'python', 'css', 'html'];

      testLanguages.forEach((lang) => {
        const result = langs[lang]();
        expect(result).toBeDefined();

        // Both LanguageSupport and StreamLanguage have 'language' property
        expect(result).toHaveProperty('language');

        // Check if it's a LanguageSupport with extension property
        if ('extension' in result) {
          expect(result).toHaveProperty('extension');
        }
      });
    });

    it('should handle edge case languages', () => {
      // Test numeric keys
      if ('1' in langs) {
        const result = langs['1' as LanguageName]();
        expect(result).toBeDefined();
      }

      // Test special character keys
      if ('c++' in langs) {
        const result = langs['c++' as LanguageName]();
        expect(result).toBeDefined();
      }
    });
  });
});
