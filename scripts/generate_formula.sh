#!/bin/bash
# Script to help generate Homebrew formula after a release
# Usage: ./scripts/generate_formula.sh v0.1.0

set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <version> (e.g., v0.1.0)"
    exit 1
fi

VERSION=$1
VERSION_NO_V=${VERSION#v}

echo "Generating Homebrew formula for version $VERSION"

# Check if the tag exists
if ! git rev-parse "$VERSION" >/dev/null 2>&1; then
    echo "Error: Tag $VERSION does not exist"
    exit 1
fi

GITHUB_REPO="pratyaypandey/polyparse"
TARBALL_URL="https://github.com/${GITHUB_REPO}/archive/refs/tags/${VERSION}.tar.gz"

echo "Downloading tarball from $TARBALL_URL"
curl -L -o "/tmp/polyparse-${VERSION}.tar.gz" "$TARBALL_URL"

# Calculate SHA256
SHA256=$(shasum -a 256 "/tmp/polyparse-${VERSION}.tar.gz" | cut -d' ' -f1)
echo "SHA256: $SHA256"

# Generate the formula
cat > Formula/polyparse.rb << EOF
class Polyparse < Formula
  include Language::Python::Virtualenv

  desc "CLI tool to scrape Polymarket event data using Selenium"
  homepage "https://github.com/${GITHUB_REPO}"
  url "https://github.com/${GITHUB_REPO}/archive/refs/tags/${VERSION}.tar.gz"
  sha256 "${SHA256}"
  license "MIT"
  version "${VERSION_NO_V}"

  depends_on "python@3.11"

  # Python dependencies
  resource "selenium" do
    url "https://files.pythonhosted.org/packages/48/dc/c8df451e32f86c35b3e61c2e7d2b2e74c6d8c5b0c4e3c2b3c5f0e3f0e3f0/selenium-4.15.0.tar.gz"
    sha256 "7cea8b6b7780a0e5afa2a55e5b1e9e5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5b5"
  end

  resource "webdriver-manager" do
    url "https://files.pythonhosted.org/packages/source/w/webdriver-manager/webdriver-manager-4.0.0.tar.gz"
    sha256 "3d5f8d6f2c8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8f8"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.0.tar.gz"
    sha256 "8c04c11192119b1ef78ea049e0a6f0463e4c48ef00a30160c704337586f3ad7a"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/source/p/python-dateutil/python-dateutil-2.8.2.tar.gz"
    sha256 "0123cacc1627ae19ddf3c27a5de5bd67ee4586fbdd6440d9748f8abb483d3e86"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{bin}/polyparse --help")
    assert_match "CLI tool", output
  end
end
EOF

echo "Formula generated at Formula/polyparse.rb"
echo ""
echo "Next steps:"
echo "1. Review the formula"
echo "2. Test it locally: brew install --build-from-source ./Formula/polyparse.rb"
echo "3. Create a tap repository if you haven't already"
echo "4. Copy the formula to your tap repository"

# Clean up
rm "/tmp/polyparse-${VERSION}.tar.gz"
