class Polyparse < Formula
  include Language::Python::Virtualenv

  desc "CLI tool to scrape Polymarket event data using Selenium"
  homepage "https://github.com/yourusername/polyparse"
  url "https://github.com/yourusername/polyparse/archive/refs/tags/v0.1.0.tar.gz"
  sha256 "" # This will be calculated automatically by Homebrew
  license "MIT"

  depends_on "python@3.11"
  depends_on "chrome-driver"

  resource "selenium" do
    url "https://files.pythonhosted.org/packages/source/s/selenium/selenium-4.15.0.tar.gz"
    sha256 "e1a0672ae6c5b1f9cd1c3f9d8e3f5a9e3b4e0d0e4f0d0f0f0d0f0f0f0f0f0f0"
  end

  resource "webdriver-manager" do
    url "https://files.pythonhosted.org/packages/source/w/webdriver-manager/webdriver-manager-4.0.0.tar.gz"
    sha256 "e1a0672ae6c5b1f9cd1c3f9d8e3f5a9e3b4e0d0e4f0d0f0f0d0f0f0f0f0f0f0"
  end

  resource "click" do
    url "https://files.pythonhosted.org/packages/source/c/click/click-8.1.0.tar.gz"
    sha256 "e1a0672ae6c5b1f9cd1c3f9d8e3f5a9e3b4e0d0e4f0d0f0f0d0f0f0f0f0f0f0"
  end

  resource "python-dateutil" do
    url "https://files.pythonhosted.org/packages/source/p/python-dateutil/python-dateutil-2.8.2.tar.gz"
    sha256 "e1a0672ae6c5b1f9cd1c3f9d8e3f5a9e3b4e0d0e4f0d0f0f0d0f0f0f0f0f0f0"
  end

  def install
    virtualenv_install_with_resources
  end

  test do
    output = shell_output("#{bin}/polyparse --help")
    assert_match "CLI tool to scrape Polymarket event data", output
  end
end
