"use client";

import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table"
import { Leilao, RequestedLeilao } from "@/lib/types";
import { calc_remaning } from "@/lib/utils";
import { useEffect, useState } from "react";
import { Button } from "../ui/button";
import { BellIcon, BellOffIcon, SendIcon } from "lucide-react";
import {
    Dialog,
    DialogClose,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import { Input } from "../ui/input";
import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "../ui/form";

import { zodResolver } from "@hookform/resolvers/zod"
import { useForm } from "react-hook-form"
import { z } from "zod"
import axios from "axios";
import { toast } from "sonner"

const formSchema = z.object({
    lance: z.number().min(0.01, {
        error: "O valor mínimo para um leilão é R$0.01."
    })
})

interface ConsultSectionInterface {
    client_id: string;
}

export function ConsultSection({ client_id }: ConsultSectionInterface) {
    const [leiloes, set_leiloes] = useState<Leilao[]>([]);
    const [time, set_time] = useState<Date>(new Date);

    const get_leiloes = async () => {
        const response = await axios.get("http://localhost:8888/leilao");

        const leiloes: RequestedLeilao[] = response.data;
        let data = []

        for (let i = 0; i < leiloes.length; i++) {
            const leilao = leiloes[i];

            data.push({
                "name": leilao.name,
                "description": leilao.description,
                "value": leilao.value,
                "start": new Date(leilao.start * 1000),
                "end": new Date(leilao.end * 1000),
                "id": leilao.id
            })
        }

        set_leiloes(data);
    }

    useEffect(() => {
        const interval = setInterval(() => {
            set_time(new Date());
        }, 1000);

        get_leiloes();

        return () => {
            clearInterval(interval);
        };
    }, []);

    const form = useForm<z.infer<typeof formSchema>>({
        resolver: zodResolver(formSchema),
        defaultValues: {
            lance: 0.01,
        },
    })

    async function onLance(values: z.infer<typeof formSchema>, ref_leilao: Leilao) {
        const response = await axios.post("http://localhost:8888/lance", {
            "leilao_id": ref_leilao.id,
            "client_id": client_id,
            "value": values.lance
        });

        if (response.status == 201)
        {
            toast.success("Lance realizado!");
        }
        else
        {
            toast.error("Oops!");
        }
    }

    async function onPermitNotification(ref_leilao: Leilao) {
        const response = await axios.post(`http://localhost:8888/notificacoes/${ref_leilao.id}`, {}, {
            headers: {
                "Authorization": client_id
            }
        });

        if (response.status == 200)
        {
            toast.success(`Você indicou interesse ao leilão ${ref_leilao.name}`);
        }
        else
        {
            toast.error(`Oops!`);
        }
    }

    async function onCancelNotification(ref_leilao: Leilao) {
        const response = await axios.delete(`http://localhost:8888/notificacoes/${ref_leilao.id}`, {
            headers: {
                "Authorization": client_id
            }
        });

        if (response.status == 200)
        {
            toast.success(`Você cancelou interesse ao leilão ${ref_leilao.name}`);
        }
        else
        {
            toast.error(`Oops!`);
        }
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle>Leilões ativos</CardTitle>
                <CardDescription>
                    Lista dos leilões que estão ativos.
                </CardDescription>
            </CardHeader>
            <CardContent className="grid gap-6">
                <Table>
                    <TableHeader>
                        <TableRow>
                            <TableHead className="w-[100px]">Nome do produto</TableHead>
                            <TableHead>Descrição</TableHead>
                            <TableHead>Valor</TableHead>
                            <TableHead>Tempo restante</TableHead>
                            <TableHead></TableHead>
                            <TableHead></TableHead>
                            <TableHead></TableHead>
                        </TableRow>
                    </TableHeader>
                    <TableBody>
                        {leiloes.length > 0 && leiloes.map((leilao) => (
                            <TableRow key={leilao.id}>
                                <TableCell>{leilao.name}</TableCell>
                                <TableCell>{leilao.description}</TableCell>
                                <TableCell>R${leilao.value.toFixed(2)}</TableCell>
                                <TableCell>{calc_remaning(time, leilao.end)}</TableCell>
                                <TableCell>
                                    <Dialog>
                                        <DialogTrigger asChild>
                                            <Button variant={"outline"}>
                                                <SendIcon /> Realizar um lance
                                            </Button>
                                        </DialogTrigger>
                                        <DialogContent>
                                            <DialogHeader>
                                                <DialogTitle>Deseja realizar um lance?</DialogTitle>
                                                <DialogDescription>
                                                    Esta ação não garante que você ganhe.
                                                </DialogDescription>
                                            </DialogHeader>

                                            <Form {...form}>
                                                <form onSubmit={form.handleSubmit(async (data) => await onLance(data, leilao))} className="space-y-8">
                                                    <FormField
                                                        control={form.control}
                                                        name="lance"
                                                        render={({ field }) => (
                                                            <FormItem>
                                                                <FormLabel>Valor a ser lançado</FormLabel>
                                                                <FormControl>
                                                                    <Input type="number" step={0.01} {...field} onChange={event => field.onChange(Number(event.target.value))} />
                                                                </FormControl>
                                                                <FormDescription>
                                                                    Valor do lance.
                                                                </FormDescription>
                                                                <FormMessage />
                                                            </FormItem>
                                                        )}
                                                    />

                                                    <DialogFooter className="sm:justify-start">
                                                        <DialogClose asChild>
                                                            <Button type="submit" variant="default">
                                                                Lançar
                                                            </Button>
                                                        </DialogClose>
                                                        <DialogClose asChild>
                                                            <Button type="button" variant="secondary">
                                                                Cancelar
                                                            </Button>
                                                        </DialogClose>
                                                    </DialogFooter>
                                                </form>
                                            </Form>
                                        </DialogContent>
                                    </Dialog>
                                </TableCell>
                                <TableCell>
                                    <Button size="icon" variant={"outline"} onClick={(e) => onPermitNotification(leilao)}>
                                        <BellIcon />
                                    </Button>
                                </TableCell>
                                <TableCell>
                                    <Button size="icon" variant={"outline"} onClick={(e) => onCancelNotification(leilao)}>
                                        <BellOffIcon />
                                    </Button>
                                </TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </CardContent>
        </Card>
    )
}