import QtQuick 2.15
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.15

ApplicationWindow {
    id: root
    visible: true
    width: 800
    height: 600
    maximumHeight: height
    maximumWidth: width
    minimumHeight: height
    minimumWidth: width
    title: ":)"
    color: "aliceblue"
    property alias stack_view: stack_view

    Connections {
        target: client_model
    }

    StackView {
        id: stack_view
        anchors.fill: parent
        initialItem: main_view
    }

    Item {
        id: main_view
        anchors.fill: parent

        ListView {
            id: list_view
            height: 500
            width: parent.width
            model: client_model.message_list
            delegate: Text {
                height: 30
                text: modelData.msg
            }
            onCountChanged: {
                list_view.positionViewAtEnd()
            }
            ScrollBar.vertical: ScrollBar {
                active: true
            }
        }

        TextField {
            id: input
            anchors.bottom: parent.bottom
            width: parent.width
            placeholderText: "text"
            height: 100
            property string value: ""
            verticalAlignment: TextInput.AlignTop
            onTextChanged: value = text
            onAccepted: {
                client_model.submit_message(input.value)
                input.text = ""
            }
        }

        Image {
            id: user_button
            source: "./static/user.png"
            width: 50
            fillMode: Image.PreserveAspectFit
            anchors.right: parent.right
            anchors.top: parent.top
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    username_field.text = ""
                    passwd_field.text = ""
                    stack_view.push(login_view)
                }
            }
        }

        Image {
            source: "./static/send.png"
            width: 60
            fillMode: Image.PreserveAspectFit
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    client_model.submit_message(input.value)
                    input.text = ""
                }
            }
        }
    }

    Item {
        id: login_view
        anchors.fill: parent
        visible: false

        Image {
            source: "./static/back.png"
            width: 50
            height: 50
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    stack_view.pop();
                }
            }
        }

        Column {
            width: 400
            spacing: 20
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter

            Text {
                width: 400
                height: 30
                verticalAlignment: Text.AlignVCenter
                text: qsTr("登录页")
                font.pixelSize: 17
                horizontalAlignment: Text.AlignHCenter
            }

            TextField {
                id: username_field
                placeholderText: "用户名"
                width: 400
                height: 30
                property string value: ""
                onTextChanged: value = text
            }

            TextField {
                id: passwd_field
                placeholderText: "密码"
                echoMode: TextInput.Password
                width: 400
                height: 30
                property string value: ""
                onTextChanged: value = text
            }

            Row {
                width: 300
                height: 60
                spacing: 200
                anchors.horizontalCenter: parent.horizontalCenter

                Image {
                    source: "./static/login.png"
                    width: 60
                    height: 60
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            client_model.user_login(username_field.value, passwd_field.value);
                            stack_view.pop();
                        }
                    }
                }

                Image {
                    source: "./static/signup.png"
                    width: 60
                    height: 60
                    MouseArea {
                        anchors.fill: parent
                        onClicked: {
                            client_model.user_register(username_field.value, passwd_field.value);
                            stack_view.pop();
                        }
                    }
                }
            }
        }
    }
}