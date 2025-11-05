# Contributing to Brain-AI RAG++

Thank you for your interest in contributing to Brain-AI RAG++! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inspiring community for all. Please be respectful and constructive in your interactions.

### Our Standards

- Be respectful and inclusive
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

## Getting Started

### Prerequisites

- C++ compiler with C++17 support
- Python 3.12+
- Node.js 18+
- Git
- Docker (for testing containerized builds)

### Finding Issues to Work On

- Check the [Issues](https://github.com/yourusername/C-AI-BRAIN-2/issues) page
- Look for issues labeled `good first issue` or `help wanted`
- Ask in Discussions if you want to work on something new

## Development Setup

### 1. Fork and Clone

```bash
# Fork on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/C-AI-BRAIN-2.git
cd C-AI-BRAIN-2

# Add upstream remote
git remote add upstream https://github.com/yourusername/C-AI-BRAIN-2.git
```

### 2. Create Development Environment

```bash
# Install dependencies
./start_dev.sh

# Run tests to verify setup
./test_e2e_full.sh
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Use the bug report template**
3. **Include**:
   - Clear description
   - Steps to reproduce
   - Expected vs actual behavior
   - System information
   - Relevant logs

### Suggesting Enhancements

1. **Search existing issues** for similar suggestions
2. **Use the feature request template**
3. **Explain**:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative solutions considered
   - Impact on existing functionality

### Improving Documentation

- Fix typos or clarify existing docs
- Add examples or tutorials
- Improve API documentation
- Translate documentation

## Code Style

### C++

Follow the Google C++ Style Guide:

```bash
# Format code
clang-format -i src/**/*.cpp include/**/*.hpp

# Style guide
- Use snake_case for variables and functions
- Use PascalCase for classes
- Use UPPER_CASE for constants
- Maximum 100 characters per line
```

### Python

Follow PEP 8 with black formatting:

```bash
# Format code
black .

# Check style
flake8 .

# Type checking
mypy .
```

### TypeScript/JavaScript

Use Prettier and ESLint:

```bash
# Format code
npm run format

# Check lint
npm run lint
```

## Testing

### Running Tests

```bash
# C++ tests
cd brain-ai/build
ctest --output-on-failure

# Python tests
cd brain-ai-rest-service
pytest

# GUI tests
cd brain-ai-gui
npm test

# End-to-end
./test_e2e_full.sh
```

### Writing Tests

- **Unit tests**: Test individual functions/methods
- **Integration tests**: Test component interactions
- **E2E tests**: Test full user workflows

### Test Requirements

- All new features must have tests
- Aim for >80% code coverage
- Tests should be fast and reliable
- Use descriptive test names

## Submitting Changes

### Commit Messages

Follow conventional commits:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Build/tooling changes

**Examples:**
```bash
feat(api): add batch indexing endpoint

Implements batch document indexing for improved performance.
Supports up to 1000 documents per request.

Closes #123

fix(gui): resolve healthcheck failure

Changes healthcheck from wget to curl for Alpine compatibility.

test(core): add vector search benchmarks
```

### Pull Request Process

1. **Update your branch**:
```bash
git fetch upstream
git rebase upstream/main
```

2. **Run all tests**:
```bash
./test_e2e_full.sh
```

3. **Push changes**:
```bash
git push origin feature/your-feature-name
```

4. **Create Pull Request**:
   - Use the PR template
   - Link related issues
   - Provide clear description
   - Add screenshots for UI changes

### Pull Request Checklist

- [ ] Code follows style guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Commit messages follow conventions
- [ ] All tests pass
- [ ] No merge conflicts
- [ ] Reviewed own code

## Review Process

### Timeline

- Initial review: Within 48 hours
- Follow-up reviews: Within 24 hours
- Merge: After 1+ approvals

### Review Criteria

- Code quality and style
- Test coverage
- Documentation completeness
- Performance impact
- Backward compatibility
- Security implications

### Addressing Feedback

- Be responsive to comments
- Ask questions if unclear
- Make requested changes
- Re-request review when ready

## Development Tips

### Debugging

```bash
# C++ with gdb
gdb ./brain_ai_demo

# Python with pdb
python -m pdb app.py

# Check logs
tail -f logs/rest-api.log
```

### Performance Profiling

```bash
# C++ profiling
valgrind --tool=callgrind ./brain_ai_demo

# Python profiling
python -m cProfile -o profile.stats app.py
```

### Common Issues

**Build fails:**
- Check dependencies are installed
- Clear build cache: `rm -rf brain-ai/build`
- Update submodules: `git submodule update --init`

**Tests fail:**
- Ensure services are running
- Check environment variables
- Review test logs

**GUI not loading:**
- Verify REST API is running
- Check browser console
- Verify CORS settings

## Recognition

Contributors will be:
- Listed in CONTRIBUTORS.md
- Credited in release notes
- Mentioned in the project README

## Questions?

- **GitHub Discussions**: For questions and ideas
- **GitHub Issues**: For bug reports and feature requests
- **Email**: dev@example.com

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Brain-AI RAG++! 🎉
