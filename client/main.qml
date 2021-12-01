import QtQuick 2.15
import QtQuick.Dialogs 1.2
import QtQuick.Controls 2.15

ApplicationWindow {
    id: root
    visible: true
    width: 400
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

        Text {
            anchors.verticalCenter: user_button.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter
            text: "客服系统"
            font.pixelSize: 17
        }

        Rectangle {
            anchors.top: user_button.bottom
            anchors.bottom: text_field_rec.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: 10
            radius: 10
            border.color: "black"
            border.width: 1

            ListView {
                id: list_view
                anchors.fill: parent
                anchors.topMargin: 10
                anchors.bottomMargin: 10
                model: client_model.message_list
                clip: true
                delegate: Item {
                    width: 380
                    height: Math.max(avatar.height, message_rec.height) + 10

                    Image {
                        id: avatar
                        source: modelData.author ? "./static/client.png" : "./static/support.png"
                        width: 30
                        fillMode: Image.PreserveAspectFit
                        anchors.right: modelData.author ? parent.right : undefined
                        anchors.rightMargin: modelData.author ? 10 : undefined
                        anchors.left: modelData.author ? undefined : parent.left
                        anchors.leftMargin: modelData.author ? undefined : 10
                    }

                    Rectangle {
                        id: message_rec
                        color: "aliceblue"
                        height: message.contentHeight + 10
                        width: 250
                        radius: 10
                        border.color: "black"
                        border.width: 1
                        anchors.right: modelData.author ? avatar.left : undefined
                        anchors.rightMargin: modelData.author ? 10 : undefined
                        anchors.left: modelData.author ? undefined : avatar.right
                        anchors.leftMargin: modelData.author ? undefined : 10

                        Text {
                            id: message
                            anchors.left: parent.left
                            anchors.leftMargin: 10
                            anchors.verticalCenter: parent.verticalCenter
                            width: 230
                            text: modelData.msg
                            wrapMode: Text.Wrap
                        }
                    }
                }
                onCountChanged: {
                    list_view.positionViewAtEnd()
                }
                ScrollBar.vertical: ScrollBar {
                    active: true
                }
            }
        }

        Rectangle {
            id: text_field_rec
            anchors.bottom: parent.bottom
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.leftMargin: 10
            anchors.rightMargin: 10
            anchors.bottomMargin: 10
            height: 40
            radius: 10
            border.color: "black"
            border.width: 1

            TextField {
                id: input
                anchors.verticalCenter: parent.verticalCenter
                anchors.left: parent.left
                anchors.leftMargin: 5
                anchors.right: send_button.left
                anchors.rightMargin: 5
                height: 30
                placeholderText: "text"
                property string value: ""
                verticalAlignment: TextInput.AlignTop
                onTextChanged: value = text
                onAccepted: {
                    client_model.submit_message(input.value)
                    input.text = ""
                }
            }

            Image {
                id: send_button
                source: "./static/send.png"
                height: 30
                fillMode: Image.PreserveAspectFit
                anchors.right: parent.right
                anchors.rightMargin: 5
                anchors.verticalCenter: parent.verticalCenter
                MouseArea {
                    anchors.fill: parent
                    onClicked: {
                        client_model.submit_message(input.value)
                        input.text = ""
                    }
                }
            }
        }

        Image {
            id: user_button
            source: "./static/user.png"
            width: 40
            fillMode: Image.PreserveAspectFit
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.rightMargin: 10
            anchors.topMargin: 10
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    username_field.text = ""
                    passwd_field.text = ""
                    stack_view.push(login_view)
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
            width: 40
            fillMode: Image.PreserveAspectFit
            anchors.left: parent.left
            anchors.top: parent.top
            anchors.leftMargin: 10
            anchors.topMargin: 10
            MouseArea {
                anchors.fill: parent
                onClicked: {
                    stack_view.pop();
                }
            }
        }

        Column {
            width: 250
            spacing: 20
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter

            Text {
                width: 250
                height: 30
                verticalAlignment: Text.AlignVCenter
                text: qsTr("登录页")
                font.pixelSize: 17
                horizontalAlignment: Text.AlignHCenter
            }

            TextField {
                id: username_field
                placeholderText: "用户名"
                width: 250
                height: 30
                property string value: ""
                onTextChanged: value = text
            }

            TextField {
                id: passwd_field
                placeholderText: "密码"
                echoMode: TextInput.Password
                width: 250
                height: 30
                property string value: ""
                onTextChanged: value = text
            }

            Row {
                width: 250
                height: 60
                spacing: 130
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