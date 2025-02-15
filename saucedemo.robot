*** Settings ***
Library    SeleniumLibrary

*** Variables ***
${URL}             https://www.saucedemo.com/
${BROWSER}         chrome
${USERNAME}        standard_user
${PASSWORD}        secret_sauce
${SLEEP}           0s

*** Test Cases ***
TC001 Shopping Cart
    [Setup]    Run keywords    Open Saucedemo Website    AND    Login
    Add Item To Cart    Sauce Labs Bolt T-Shirt
    Add Item To Cart    Test.allTheThings() T-Shirt (Red)
    Go to Cart
    Proceed To Checkout
    Fill Firstname    Tang
    Fill Lastname    SudLor
    Fill Zipcode    10900
    Click Continue
    Verify Checkout Summary    Item total: $31.98
    Complete Order And Get Message    Thank you for your order!
    [Teardown]     Close Browser

*** Keywords ***
Wait And Input
    [Arguments]    ${locator}    ${value}
    Highlight Field    ${locator}
    Wait Until Element Is Visible    ${locator}
    Input Text    ${locator}    ${value}
    Sleep    ${SLEEP}
    Remove Highlight    ${locator}

Wait And Click
    [Arguments]    ${locator}
    Highlight Field    ${locator}
    Wait Until Element Is Visible    ${locator}
    Sleep    ${SLEEP}
    Remove Highlight    ${locator}
    Click Element    ${locator}

Wait And Verify
    [Arguments]    ${locator}    ${text}
    Wait Until Element Is Visible    ${locator}
    Highlight Field    ${locator}
    Element Text Should Be    ${locator}    ${text}
    Sleep    ${SLEEP}
    Remove Highlight    ${locator}

Highlight Field
    [Arguments]    ${locator}    ${color}=yellow
    ${element}    Get WebElement    xpath=${locator}
    Execute JavaScript    arguments[0].style.backgroundColor = '${color}';    ARGUMENTS    ${element}

Remove Highlight
    [Arguments]    ${locator}
    ${element}    Get WebElement    xpath=${locator}
    Execute JavaScript    arguments[0].style.backgroundColor = '';    ARGUMENTS    ${element}

Open Saucedemo Website
    Open Browser    ${URL}    ${BROWSER}

Login
    [Arguments]    ${username}=${USERNAME}    ${password}=${PASSWORD}
    Wait And Input    //input[@name="user-name"]    ${username}
    Wait And Input    //input[@name="password"]    ${password}
    Wait And Click    //input[@name="login-button"]

Add Item To Cart
    [Arguments]    ${item_name}
    Wait And Click    //div[text()='${item_name}']/ancestor::div[contains(@class, 'inventory_item_description')]//button

Go to Cart
    Wait And Click    //a[@class="shopping_cart_link"]

Proceed To Checkout
    Wait And Click    //button[@name="checkout"]

Fill Firstname
    [Arguments]    ${first_name}
    Wait And Input    //input[@name="firstName"]    ${first_name}

Fill Lastname
    [Arguments]    ${last_name}
    Wait And Input    //input[@name="lastName"]    ${last_name}

Fill Zipcode
    [Arguments]    ${province}
    Wait And Input    //input[@name="postalCode"]    ${province}

Click Continue
    Wait And Click    //input[@name="continue"]

Verify Checkout Summary
    [Arguments]    ${expected_price}
    Wait And Verify    //*[@id="checkout_summary_container"]/div/div[2]/div[6]    ${expected_price}

Complete Order And Get Message
    [Arguments]    ${message}
    Wait And Click    //button[@name="finish"]
    Wait And Verify    //*[@id="checkout_complete_container"]/h2    ${message}
