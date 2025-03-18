*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${BROWSER}    chrome
${OPTIONS}    binary_location=${CHROME_BIN}

*** Test Cases ***
Open Google with Playwright Chromium
    Open Browser    https://www.google.com    ${BROWSER}    options=${OPTIONS}
    Sleep    5s
    Capture Page Screenshot
    Close Browser
