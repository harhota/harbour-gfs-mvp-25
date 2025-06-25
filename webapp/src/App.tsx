import React, { useState, useEffect } from "react";
import {
    Theme,
    Button,
    TextField,
    TextArea,
    Flex,
    Heading,
    Text,
} from "@radix-ui/themes";
import {
    useUploadFile,
    useReadFile,
    useDeleteFile,
    useFileSize,
} from "./hooks";

export default function App() {
    const [filename, setFilename] = useState("");
    const [content, setContent] = useState("");
    const [message, setMessage] = useState("");
    const [errorMessage, setErrorMessage] = useState("");

    const uploadMutation = useUploadFile();
    const deleteMutation = useDeleteFile();
    const readQuery = useReadFile(filename, false);
    const { error: readQueryError } = readQuery;
    const sizeQuery = useFileSize(filename, false);

    useEffect(() => {
        if (readQuery.data !== undefined) {
            // const parsedReadData = JSON.parse(readQuery.data)
            if (readQuery.data) {
                setContent(readQuery.data);
            }
        }
    }, [readQuery.data]);

    const handleUpload = async () => {
        setMessage("");
        setErrorMessage("");
        try {
            await uploadMutation.mutateAsync({ filename, data: content });
            setMessage("File uploaded");
        } catch (e: any) {
            const parsedError = JSON.parse(e.message);
            setErrorMessage(parsedError.detail);
        }
    };

    const handleRead = async () => {
        setMessage("");
        setErrorMessage("");
        try {
            await readQuery.refetch();
        } catch (e: any) {
            const parsedError = JSON.parse(e.message);
            setErrorMessage(parsedError.detail);
        }
    };

    const handleDelete = async () => {
        setMessage("");
        setErrorMessage("");
        try {
            await deleteMutation.mutateAsync(filename);
            setMessage("File deleted");
        } catch (e: any) {
            const parsedError = JSON.parse(e.message);
            setErrorMessage(parsedError.detail);
        }
    };

    const handleSize = async () => {
        setMessage("");
        setErrorMessage("");
        try {
            await sizeQuery.refetch();
        } catch (e: any) {
            const parsedError = JSON.parse(e.message);
            setErrorMessage(parsedError.detail);
        }
    };

    return (
        <div>
            <Heading>Harbour DFS Client</Heading>
            <Flex
                direction="column"
                gap="3"
                style={{ maxWidth: 600, margin: "0 auto", padding: "1rem" }}
            >
                <TextField.Root
                    placeholder="Filename"
                    value={filename}
                    onChange={(e) => setFilename(e.target.value)}
                />
                <TextArea
                    placeholder="File contents"
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={10}
                />
                <Flex gap="2" wrap="wrap">
                    <Button onClick={handleUpload}>Upload</Button>
                    <Button onClick={handleRead}>Read</Button>
                    <Button onClick={handleDelete}>Delete</Button>
                    <Button onClick={handleSize}>Size</Button>
                </Flex>
                {sizeQuery.data !== undefined && (
                    <Text size="2">Size: {sizeQuery.data}</Text>
                )}
                {readQueryError && (
                    <Text size="2" color="red">
                        {readQueryError.message}
                    </Text>
                )}
                {sizeQuery.error && (
                    <Text size="2" color="red">
                        {sizeQuery.error.message}
                    </Text>
                )}
                {message && <Text size="2">{message}</Text>}
                {errorMessage && (
                    <Text size="2" color="red">
                        {errorMessage}
                    </Text>
                )}
            </Flex>
        </div>
    );
}
