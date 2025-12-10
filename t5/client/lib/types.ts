export interface Leilao {
    name: string;
    description: string;
    value: number;
    start: Date;
    end: Date;
    id?: string;
}

export interface RequestedLeilao {
    name: string;
    description: string;
    value: number;
    start: number;
    end: number;
    id?: string;
}

export interface Message {
    event_name: string;
    [key: string]: any;
}